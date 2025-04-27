# config.py
"""
Parametres de calcul d'indice spatial optimisé pour la chlorophylle.
Auteur : Marc Francescon
Date : Avril 2025
"""

import numpy as np

ALPHA = 1.8  # Coefficient entre la taille du rayon r1 (cercle intérieur) et r2 (cercle extérieur)
R1_LIST = np.arange(2, 7, 0.5)  # Liste des rayons r1 testés (en pixels)
SEUIL_COUVERTURE = 0.5  # Seuil minimal de couverture de données valides (50%)
PENAL_LAMBDA = 0.05  # Coefficient de pénalisation pour grands rayons
R_CRIT = 3  # Rayon critique (en pixels) à partir duquel la pénalisation commence


