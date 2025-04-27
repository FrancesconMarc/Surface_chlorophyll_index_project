Surface Chlorophyll Index Project
Présentation
Ce projet a pour objectif de calculer un indice spatial optimisé à partir des données satellitaires de chlorophylle de surface (MODIS Aqua, produit L3m, résolution 4 km). L'approche repose sur un rapport entre les moyennes de chlorophylle intérieure et extérieure à différentes échelles spatiales, permettant d'identifier des structures enrichies qui ne sont pas détectables par une analyse classique basée uniquement sur les moyennes de chlorophylle. Cela permet de révéler des anomalies spatiales fines, invisibles autrement.

Objectifs scientifiques
	•	Détecter et caractériser les structures spatiales d'enrichissement de la chlorophylle.
	•	Générer des fichiers NetCDF quotidiens contenant l'indice spatial optimisé.
	•	Vérifier, nettoyer et, si besoin, reconstituer les fichiers de chlorophylle bruts et les fichiers d'indice.
	•	Préparer une base de données cohérente pour des analyses statistiques ou écologiques ultérieures.

Organisation du projet
Surface_chlorophyll_index_project/
|
|├— chlorindex/
|   |├— config.py                 # Définition des paramètres globaux du calcul
|   |├— core.py                   # Fonctions principales de calcul de l'indice spatial
|   └— run_index.py               # Script d'exécution du traitement journalier
|
|├— Download_verification/
|   |├— download_files.py          # Script de téléchargement automatique des données chlorophylle
|   |├— download_function.py       # Fonction dédiée au téléchargement sécurisé
|   |├— verification_fichier_chla.py   # Vérification qualité des fichiers chlorophylle bruts
|   └— verification_fichier_Index.py  # Vérification qualité et correction des fichiers d'indice spatial
|
└— README.md                      # Présentation du projet

Prérequis
	•	Python ≥ 3.9
	•	Librairies Python :
	◦	numpy
	◦	xarray
	◦	scipy
	◦	tqdm
	◦	requests
	◦	pandas
Installation recommandée via pip ou environnement conda.

Mode opératoire
1. Télécharger les données MODIS chlorophylle
python Download_verification/download_files.py
2. Vérifier les fichiers chlorophylle téléchargés
python Download_verification/verification_fichier_chla.py
3. Calculer l'indice spatial optimisé pour chaque jour
python chlorindex/run_index.py
4. Vérifier et corriger les fichiers d'indice générés
python Download_verification/verification_fichier_Index.py

Remarques méthodologiques
	•	L'indice spatial est construit sur un ratio de moyennes, pénalisé par un terme exponentiel pour éviter les biais liés aux grandes échelles spatiales.
	•	Les fichiers endommagés ou incomplets sont systématiquement détectés, supprimés et reconstitués à partir des données brutes disponibles.
	•	La rigueur de traitement a été une priorité tout au long de la structuration de ce projet.

Auteur
Marc Francescon Avril 2025

