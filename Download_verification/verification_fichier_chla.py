# verification_fichier_chla.py
"""
Script de vérification et de réparation automatique des fichiers chlorophylle (chlor_a) téléchargés.
Supprime les fichiers doublons, incomplets ou endommagés, et re-télécharge les fichiers manquants.
Auteur : Marc Francescon
Date : Avril 2025
"""
import os
import re
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from tqdm import tqdm
from pathlib import Path
import logging
from download_function import telecharger_fichier

# === Paramètres ===
download_folder = "/Users/marcfrancescon/Desktop/chla_2003_2013"
url_file = "/Users/marcfrancescon/Desktop/lien_chla_2003_2013.txt"
TAILLE_MIN = 1_000_000
variable = "chlor_a"

# === Logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Charger les URLs ===
with open(url_file, "r") as f:
    urls = [line.strip() for line in f if line.strip()]

# === Préparation des listes ===
doublons = []
incomplets = []
endommages = []
valides = []
fichiers_par_date = {}

# === Lister les fichiers ===
fichiers = sorted([f for f in os.listdir(download_folder) if f.endswith(".nc")])

# === Identifier les doublons ===
for f in fichiers:
    match = re.search(r"\d{8}", f)
    if match:
        d = match.group(0)
        if d in fichiers_par_date:
            doublons.append(f)
        else:
            fichiers_par_date[d] = f

# === Vérification des fichiers ===
for f in tqdm(fichiers_par_date.values(), desc="Vérification des fichiers téléchargés"):
    chemin = Path(download_folder) / f
    try:
        if os.path.getsize(chemin) < TAILLE_MIN:
            incomplets.append(f)
            continue

        ds = xr.open_dataset(chemin, engine="netcdf4")
        if variable not in ds:
            incomplets.append(f)
            ds.close()
            continue

        array = ds[variable].values
        ds.close()
        ratio_valid = 1 - np.isnan(array).mean()

        if ratio_valid < 0.01:
            incomplets.append(f)
        else:
            valides.append(f)

    except Exception as e:
        endommages.append(f)
        logging.error(f" Erreur lors de l'ouverture de {f} : {e}")

# === Vérifier les dates manquantes ===
dates_valides = []
for f in valides:
    match = re.search(r"\d{8}", f)
    if match:
        try:
            dates_valides.append(datetime.strptime(match.group(0), "%Y%m%d"))
        except ValueError:
            logging.warning(f" Mauvais format de date dans le fichier : {f}")
    else:
        logging.warning(f" Aucune date trouvée dans le nom du fichier : {f}")

if dates_valides:
    date_min = min(dates_valides)
    date_max = max(dates_valides)
    full_range = {date_min + timedelta(days=i) for i in range((date_max - date_min).days + 1)}
    existing = {datetime.strptime(re.search(r"\d{8}", f).group(0), "%Y%m%d")
                for f in fichiers_par_date.keys() if re.search(r"\d{8}", f)}
    missing = sorted(full_range - existing)
else:
    missing = []

# === Supprimer les fichiers invalides ===
for f in doublons + incomplets + endommages:
    try:
        os.remove(Path(download_folder) / f)
        logging.info(f"🗑 Fichier supprimé : {f}")
    except Exception as e:
        logging.warning(f"⚠️ Erreur lors de la suppression de {f} : {e}")

# === Reconstruire l'état du dossier ===
fichiers_restants = sorted([f for f in os.listdir(download_folder) if f.endswith(".nc")])
fichiers_par_date = {}
for f in fichiers_restants:
    match = re.search(r"\d{8}", f)
    if match:
        fichiers_par_date[match.group(0)] = f

# === Télécharger les fichiers manquants ===
for date_obj in missing:
    date_str = date_obj.strftime("%Y%m%d")
    file_name = f"AQUA_MODIS.{date_str}.L3m.DAY.CHL.chlor_a.4km.nc"
    destination = Path(download_folder) / file_name

    if not destination.exists():
        logging.info(f"⬇️ Téléchargement du fichier manquant : {file_name}")
        url = next((url for url in urls if date_str in url), None)
        if url:
            telecharger_fichier(url, destination)
        else:
            logging.warning(f"🔍 Aucun lien trouvé pour la date : {date_str}")

# === Résumé final ===
logging.info(f" Fichiers valides : {len(valides)}")
logging.info(f" Fichiers doublons supprimés : {len(doublons)}")
logging.info(f" Fichiers incomplets supprimés : {len(incomplets)}")
logging.info(f" Fichiers endommagés supprimés : {len(endommages)}")
logging.info(f" Fichiers manquants téléchargés : {len(missing)}")