Script de seed Teamworks

Fichier principal :
- teamworks/CcnsCore/seed_teamworks_reference_data.py

But :
- injecter des données de référence CCNS dans les tables historiques Teamworks
- injecter les classifications et grilles dans les tables tw_*
- injecter quelques règles par défaut

Usage :
1. lancer d'abord la montée de version / création des tables tw_*
2. exécuter ensuite le script :
   python teamworks/CcnsCore/seed_teamworks_reference_data.py

Effet :
- groupes G1 à G8 + APPRENTI
- types de contrat principaux
- grille CCNS 2026 du 1er janvier
- premières lignes de minima
- premières règles métier
