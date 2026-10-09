"""Configuration pytest commune.

Les recettes wx/Windows lourdes sont volontairement exécutées explicitement
par le workflow Windows. Elles ne doivent jamais être des fixtures autouse :
sinon chaque processus pytest relance Teamworks et multiplie le coût de la CI.
"""
