# download_files.py
"""
Script de téléchargement des fichiers chlorophylle (chlor_a) dans le dossier spécifié.
Auteur : Marc Francescon
Date : Avril 2025
"""

import os
from download_function import telecharger_fichier  # Importer la fonction de téléchargement

#  Fichier texte contenant les URLs des fichiers à télécharger
url_file = "/Users/marcfrancescon/Desktop/lien_chla_2003_2013.txt"

#  Dossier de téléchargement
download_folder = "/Users/marcfrancescon/Desktop/chla_2003_2013"

#  Lire les URLs à partir du fichier texte
with open(url_file, "r") as file:
    urls = [line.strip() for line in file if line.strip()]

#  Télécharger chaque fichier
for url in urls:
    # Extraire le nom du fichier à partir de l'URL
    filename = os.path.basename(url)
    destination = os.path.join(download_folder, filename)

    # Appel de la fonction de téléchargement
    telecharger_fichier(url, destination)

print("Téléchargement terminé.")

