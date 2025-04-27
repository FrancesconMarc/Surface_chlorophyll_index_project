# verification_fichier_Index.py
"""
Script de vérification des fichiers NetCDF générés pour l'indice spatial optimisé.
Auteur : Marc Francescon
Date : Avril 2025
"""

import os
import re
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from tqdm import tqdm
import sys


sys.path.append(os.path.abspath(".."))

from chlorindex.core import (
    calc_index_optim,
    sauvegarde_index_netcdf_standard,
    precompute_masques
)
from chlorindex.config import ALPHA, R1_LIST, SEUIL_COUVERTURE


# === Chemins ===
index_dir = "/Users/marcfrancescon/Desktop/Monde_IE_2003_2013"
chemin_chla = "/Users/marcfrancescon/Desktop/chla_2003_2013"
output_pattern = "Word_index_r1_{}.nc"
variables_attendues = ["index", "r1_best", "moy_int", "moy_ext"]
taille_min = 1_000_000  # Taille minimale en octets

# === Liste des fichiers existants ===
fichiers = sorted([
    f for f in os.listdir(index_dir)
    if f.endswith(".nc") and re.search(r"\d{8}", f)
])

fichiers_par_date = {}
doublons = []
incomplets = []
endommages = []
valides = []

# === Organisation par date ===
for f in fichiers:
    date_match = re.search(r"\d{8}", f)
    if date_match:
        d = date_match.group(0)
        if d in fichiers_par_date:
            doublons.append(f)
        else:
            fichiers_par_date[d] = f

# === Vérification des fichiers ===
for d, f in tqdm(fichiers_par_date.items(), desc="Vérification des fichiers NetCDF"):
    chemin = os.path.join(index_dir, f)
    try:
        if os.path.getsize(chemin) < taille_min:
            incomplets.append((f, "Taille insuffisante"))
            continue
        ds = xr.open_dataset(chemin)
        for var in variables_attendues:
            if var not in ds or ds[var].ndim != 3:
                incomplets.append((f, f"Variable manquante ou mauvaise dimension : {var}"))
                ds.close()
                break
        else:
            if all(np.isnan(ds[var].values).all() for var in variables_attendues):
                incomplets.append((f, "Toutes les variables sont NaN"))
            else:
                valides.append(f)
            ds.close()
    except Exception as e:
        endommages.append((f, str(e)))

# === Vérification des dates manquantes ===
dates_validees = sorted(datetime.strptime(re.search(r"\d{8}", f).group(0), "%Y%m%d") for f in valides)
if dates_validees:
    date_min = dates_validees[0]
    date_max = dates_validees[-1]
    expected_dates = [(date_min + timedelta(days=i)).strftime("%Y%m%d")
                      for i in range((date_max - date_min).days + 1)]
    dates_presentes = set(fichiers_par_date.keys())
    dates_manquantes = sorted(set(expected_dates) - dates_presentes)
else:
    dates_manquantes = []

#  Suppression des doublons et des fichiers invalides 
for f in doublons + [f for f, _ in incomplets] + [f for f, _ in endommages]:
    try:
        os.remove(os.path.join(index_dir, f))
    except:
        pass

# Regénérer les fichiers manquants 
for date_str in dates_manquantes:
    file_name = output_pattern.format(date_str)
    if not os.path.exists(os.path.join(index_dir, file_name)):
        print(f"Regénération du fichier manquant : {file_name}")

        # Trouver le fichier correspondant dans `source_dir`
        try:
            file_path = os.path.join(chemin_chla, f"AQUA_MODIS.{date_str}.L3m.DAY.CHL.chlor_a.4km.nc")
            if os.path.exists(file_path):
                # Réouvrir et traiter le fichier source
                ds = xr.open_dataset(file_path)
                chla = ds["chlor_a"].squeeze().values.astype(np.float32)
                ds.close()

                # Recalculer l'index et les autres variables
                idx_max, r1_best, moy_int, moy_ext = calc_index_optim(
                    chla, r1_vals=R1_LIST, alpha=ALPHA, seuil_couv=SEUIL_COUVERTURE, masques_cache=None
                )

                # Sauvegarder le fichier NetCDF recalculé
                lat, lon = ds["lat"].values, ds["lon"].values
                sauvegarde_index_netcdf_standard(
                    idx_max, r1_best, moy_int, moy_ext, lat, lon, file_name, index_dir
                )
            else:
                print(f"Fichier source manquant pour la date {date_str}")
        except Exception as e:
            print(f"Erreur lors de la régénération de {file_name}: {e}")

# Résumé 
import pandas as pd
from IPython.display import display

resume = {
    "Fichiers valides": len(valides),
    "Fichiers doublons supprimés": len(doublons),
    "Fichiers incomplets supprimés": len(incomplets),
    "Fichiers endommagés supprimés": len(endommages),
    "Dates manquantes à régénérer": len(dates_manquantes)
}

resume_df = pd.DataFrame(list(resume.items()), columns=["Type", "Nombre"])
display(resume_df)
