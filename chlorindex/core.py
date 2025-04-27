# core.py
"""
Module de calcul d'indice spatial optimisé pour la chlorophylle.
Auteur : Marc Francescon
Date : Avril 2025
"""

import numpy as np
import xarray as xr
from scipy.signal import fftconvolve
from datetime import datetime
import os
import re
from collections import OrderedDict

#  Paramètres globaux importés depuis config.py
from .config import ALPHA, R1_LIST, SEUIL_COUVERTURE, PENAL_LAMBDA, R_CRIT


def precompute_masques(r1_vals=None, alpha=ALPHA):
    """
    Génère un dictionnaire de masques circulaires intérieur/extérieur pour chaque rayon r1.
    """
    if r1_vals is None:
        r1_vals = R1_LIST
    cache = OrderedDict()
    for r1 in r1_vals:
        r2 = alpha * r1
        n = int(np.ceil(r2) * 2 + 1)
        centre = n // 2
        y, x = np.ogrid[:n, :n]
        dist = (x - centre)**2 + (y - centre)**2
        masque_ext = ((dist <= r2**2) & (dist > r1**2)).astype(np.float32)
        masque_int = (dist <= r1**2).astype(np.float32)
        cache[r1] = (masque_ext, masque_int)
    return cache

# Pour chaque rayon r1, calcul du ratio moyen intérieur / extérieur pondéré et pénalisé.
def calc_index_optim(chla, r1_vals=R1_LIST, alpha=ALPHA, seuil_couv=SEUIL_COUVERTURE, masques_cache=None):
    """
    Calcule l'indice spatial optimisé pixel-par-pixel sur une mappe de chlorophylle.
    Optimise le ratio entre enrichissement intérieur et enrichissement extérieur sur différents rayons r1.
    """

    if masques_cache is None:
        masques_cache = precompute_masques(r1_vals, alpha)

    nlat, nlon = chla.shape
    masque_valide = ~np.isnan(chla)
    chla0 = np.where(masque_valide, chla, 0)
    M1 = np.where(masque_valide, 1, np.nan)

    n_cand = len(r1_vals)
    indices = np.full((n_cand, nlat, nlon), np.nan, dtype=chla.dtype)
    moy_int_cand = np.full((n_cand, nlat, nlon), np.nan, dtype=chla.dtype)
    moy_ext_cand = np.full((n_cand, nlat, nlon), np.nan, dtype=chla.dtype)

    for i, r1 in enumerate(r1_vals):
        masq_ext, masq_int = masques_cache[r1]
        conv_int = fftconvolve(chla0, masq_int, mode='same')
        norm_int = fftconvolve(masque_valide.astype(float), masq_int, mode='same')
        norm_int = np.where(norm_int == 0, np.nan, norm_int)
        moy_int = (conv_int / norm_int) * M1

        conv_ext = fftconvolve(chla0, masq_ext, mode='same')
        norm_ext = fftconvolve(masque_valide.astype(float), masq_ext, mode='same')
        norm_ext = np.where(norm_ext == 0, np.nan, norm_ext)
        moy_ext = (conv_ext / norm_ext) * M1

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = moy_int / moy_ext
            ratio[np.isinf(ratio)] = np.nan
            idx_cand = ratio * np.exp(- PENAL_LAMBDA * np.maximum(0, r1 - R_CRIT))# Pénalisation exponentielle appliquée pour limiter l'optimisation vers des grands rayons r1 > R_CRIT.


        cov_int = norm_int / np.sum(masq_int)
        cov_ext = norm_ext / np.sum(masq_ext)
        idx_cand[(cov_int < seuil_couv) | (cov_ext < seuil_couv)] = np.nan

        indices[i] = idx_cand
        moy_int_cand[i] = moy_int
        moy_ext_cand[i] = moy_ext

    tous_nan = np.all(np.isnan(indices), axis=0)
    cand = np.where(np.isnan(indices), -np.inf, indices)
    idx_best = np.argmax(cand, axis=0) # Sélection du meilleur r1 (indice maximal) pour chaque pixel.
    index_max = np.max(cand, axis=0)
    index_max[tous_nan] = np.nan
    meilleur_r1 = r1_vals[idx_best]
    meilleur_r1[tous_nan] = np.nan

    i_y, i_x = np.indices((nlat, nlon))
    moy_int_best = moy_int_cand[idx_best, i_y, i_x]
    moy_ext_best = moy_ext_cand[idx_best, i_y, i_x]
    moy_int_best[tous_nan] = np.nan
    moy_ext_best[tous_nan] = np.nan

    return index_max, meilleur_r1, moy_int_best, moy_ext_best


def sauvegarde_index_netcdf_standard(idx_max, r1_best, moy_int, moy_ext, lat, lon, file, output_dir, verbose=False):
    """
    Sauvegarde standardisée du fichier NetCDF journalier contenant l'indice spatial.
    """
    date_match = re.search(r"\d{8}", file)
    if not date_match:
        raise ValueError(f" Impossible d'extraire la date du fichier : {file}")
    date_str = date_match.group(0)
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    time_coord = np.array([np.datetime64(date_obj)])

    # Création des DataArrays
    def da(data, name):
        return xr.DataArray(data[None, :, :], dims=("time", "lat", "lon"),
                            coords={"time": time_coord, "lat": lat, "lon": lon}, name=name)

    ds = xr.Dataset({
        "index": da(idx_max, "index"),
        "r1_best": da(r1_best, "r1_best"),
        "moy_int": da(moy_int, "moy_int"),
        "moy_ext": da(moy_ext, "moy_ext"),
    })

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"Word_index_r1_{date_str}.nc")

    ds.to_netcdf(output_path, format="NETCDF4", encoding={
        var: {"zlib": True, "complevel": 4} for var in ds.data_vars
    })

    if verbose:
        print(f" Fichier NetCDF sauvegardé : {output_path}")

