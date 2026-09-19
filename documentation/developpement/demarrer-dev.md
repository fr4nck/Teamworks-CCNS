# Démarrer en développement

## Lancer l'application depuis les sources

Utiliser **Python 3.11**, version exercée par la CI, et lancer `run_teamworks.py` **depuis la racine du dépôt** :

```bash
python -m pip install -r requirements.txt
python run_teamworks.py
```

!!! warning "Ne pas lancer `teamworks/Teamworks.py` directement"
    `python Teamworks.py` exécuté depuis `teamworks/` échoue sur un checkout normal (`ModuleNotFoundError: No module named 'domain'`). `teamworks/Chemins.py` (chargé par `Teamworks.py`) n'ajoute à `sys.path` que le dossier `teamworks/` et ses sous-dossiers, jamais la racine du dépôt ; or la chaîne de démarrage charge des modules comme `Ctrl/CTRL_Creation_contrat_p3_modern.py` qui importent le paquet racine `domain` (`from domain.contracts.contract_operation import ContractOperation`, etc.).
    `run_teamworks.py` insère explicitement la racine du dépôt **et** `teamworks/` dans `sys.path` (`configure_import_paths()`) avant d'exécuter `teamworks/Teamworks.py` via `runpy.run_path()` — c'est la seule commande qui garantit que les deux arborescences d'import (historique et moderne) sont résolues.

## Lancer la documentation localement

```bash
python -m venv .venv-docs
.venv-docs/bin/pip install -r requirements/docs.txt
.venv-docs/bin/mkdocs serve
```

Puis ouvrir <http://127.0.0.1:8000/>. Pour valider la construction complète (liens, nav) avant de proposer une modification :

```bash
.venv-docs/bin/mkdocs build --strict
```

## Scripts de packaging historiques, non utilisés par la CI

`setup.py` et `setup_rc1.py`/`setup_cxfreeze.bat` (packaging cx_Freeze) sont des chemins historiques/alternatifs : la CI actuelle construit le paquet Windows avec **PyInstaller**, invoqué directement dans le workflow — voir [Tests et CI](tests-ci.md).

## Repères de conventions

- Commits thématiques en français, PR en français, branche dédiée (voir `AGENTS.md` à la racine du dépôt).
- La couche `domain/`/`application/`/`infrastructure/` ne doit pas contenir de logique wxPython ni dépendre de `GestionDB` au-delà de la lecture déjà en place.
- Avant une optimisation de performance, consulter `docs/34-performance.md` et `docs/AUDIT_PERFORMANCES.md`.

## Voir aussi

[Organisation du dépôt](organisation-depot.md) · [Tests et CI](tests-ci.md) · [Contribuer et documenter](contribuer.md)
