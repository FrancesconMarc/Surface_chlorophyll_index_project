# download_function.py
"""
Script de la fonction de telechargement des fichiers chlorophylle (chlor_a) dans le dossier spécifié.
Auteur : Marc Francescon
Date : Avril 2025
"""

import os
import requests
from pathlib import Path

#  Dossier de téléchargement
download_folder = "/Users/marcfrancescon/Desktop/chla_2003_2013"
Path(download_folder).mkdir(parents=True, exist_ok=True)

#  Session avec authentification Earthdata via ~/.netrc
session = requests.Session()
session.trust_env = True  # autorise l'utilisation de .netrc et variables d'environnement

def telecharger_fichier(url, destination):
    """
    Fonction de téléchargement d'un fichier. 
    Vérifie si le fichier existe déjà et si le fichier est valide avant de télécharger.
    """
    # Vérification si le fichier existe déjà
    if os.path.exists(destination):
        print(f" Déjà présent : {os.path.basename(destination)}")
        return True

    print(f" Téléchargement : {os.path.basename(destination)}")
    try:
        r = session.get(url, stream=True, timeout=30, allow_redirects=True)
        content_type = r.headers.get("Content-Type", "")

        if r.status_code == 200 and ("netcdf" in content_type.lower() or "application/octet-stream" in content_type.lower()):
            with open(destination, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f" Fichier valide : {os.path.basename(destination)}")
            return True
        else:
            print(f" Erreur {r.status_code} - Mauvais type de fichier : {content_type}")
            return False

    except Exception as e:
        print(f" Problème avec {os.path.basename(destination)} → {e}")
        return False
