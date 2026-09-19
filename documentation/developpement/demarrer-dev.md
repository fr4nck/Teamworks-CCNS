# Démarrer en développement

## Lancer l'application depuis les sources

Utiliser **Python 3.11**, version exercée par la CI :

```bash
python -m pip install -r requirements.txt
cd teamworks
python Teamworks.py
```

Le point d'entrée moderne recommandé est `run_teamworks.py` à la racine (configure `sys.path` puis exécute `teamworks/Teamworks.py`).

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
