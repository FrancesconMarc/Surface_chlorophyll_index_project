# run_index.py
"""
Script de traitement des fichiers NetCDF de chlorophylle pour le calcul de l’indice spatial optimisé.
Auteur : Marc Francescon
Date : Avril 2025
"""

import os
import xarray as xr
import numpy as np
import re
import sys
from tqdm import tqdm

sys.path.append(os.path.abspath(".."))

from chlorindex.core import (
    calc_index_optim,
    sauvegarde_index_netcdf_standard,
    precompute_masques
)
from chlorindex.config import ALPHA, R1_LIST, SEUIL_COUVERTURE

# === Chemins ===
chemin_chla = "/Users/marcfrancescon/Desktop/chla_2003_2013"
output_dir = "/Users/marcfrancescon/Desktop/Monde_IE_2003_2013"
variable = "chlor_a"

# === Lister les fichiers à traiter ===
files = sorted([
    f for f in os.listdir(chemin_chla)
    if f.endswith(".nc") and "L3m" in f
])

# === Lire un fichier pour récupérer les coordonnées ===
sample = xr.open_dataset(os.path.join(chemin_chla, files[0]))
lat = sample["lat"].values
lon = sample["lon"].values
sample.close()

# === Pré-calcul des masques ===
masques_cache = precompute_masques(R1_LIST, ALPHA)

# === Traitement principal ===
for file in tqdm(files, desc="Traitement fichiers", unit="fichier"):
    input_path = os.path.join(chemin_chla, file)
    
    # Générer le nom de sortie basé sur la date
    date_match = re.search(r"\d{8}", file)
    if not date_match:
        print(f"⏭️  Fichier ignoré (pas de date trouvée) : {file}")
        continue

    date_str = date_match.group(0)
    output_name = f"Word_index_r1_{date_str}.nc"
    output_path = os.path.join(output_dir, output_name)

    # Sauter si le fichier de sortie existe déjà
    if os.path.exists(output_path):
        print(f" Déjà traité : {output_name}")
        continue

    try:
        ds = xr.open_dataset(input_path, engine="netcdf4")

        if variable not in ds:
            raise KeyError(f"La variable '{variable}' est absente du fichier {file}")
        chla = ds[variable].squeeze().values.astype(np.float32)
        ds.close()
    except Exception as e:
        print(f" Erreur à l’ouverture de {file} : {e}")
        continue

    # Calcul de l'indice spatial optimisé
    idx_max, r1_best, moy_int, moy_ext = calc_index_optim(
        chla,
        r1_vals=R1_LIST,
        alpha=ALPHA,
        seuil_couv=SEUIL_COUVERTURE,
        masques_cache=masques_cache
    )

    # Sauvegarde du fichier de sortie
    try:
        sauvegarde_index_netcdf_standard(
            idx_max, r1_best, moy_int, moy_ext,
            lat, lon, output_name, output_dir,verbose=False 
        )
        print(f" Sauvegardé : {output_name}")
    except Exception as e:
        print(f" Erreur lors de la sauvegarde de {output_name} : {e}")
