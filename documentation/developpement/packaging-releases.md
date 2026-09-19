# Packaging et releases

## Packaging Windows

Le paquet Windows (portable ZIP + installateur Inno Setup, `packaging/windows/Teamworks-CCNS.iss`) est construit par le job `build-windows` de la CI avec **PyInstaller**, jamais automatiquement sur chaque PR — voir [Tests et CI](tests-ci.md). Il valide un manifeste de modules internes attendus, teste le démarrage de l'exécutable et génère des sommes SHA-256.

Les scripts `setup.py`, `setup_rc1.py` et `setup_cxfreeze.bat` (packaging cx_Freeze) sont des chemins historiques/alternatifs, **non utilisés par la CI actuelle**.

## Releases

- `VERSION` (racine du dépôt) est la référence canonique de version — son contenu varie selon la branche, ne le supposez jamais fixe.
- Trois canaux (`docs/RELEASE-CHANNELS.md`) : `-dev` (développement), `-rc.N` (candidate à tester sur copie de base), version sans suffixe (stable validée).
- Le passage en stable exige la validation du parcours décrit dans `docs/TEST-RELEASE-0.9.0-RC1.md` et le respect des 5 niveaux de qualification d'AGENTS.md (code modifié → tests automatisés → exécutable construit → parcours Windows réel → recette utilisateur).
- Notes de version disponibles dans `docs/RELEASE_0.9.1*.md`.

## Voir aussi

[Tests et CI](tests-ci.md) · [Mises à jour](../demarrage/mise-a-jour.md) · [Organisation du dépôt](organisation-depot.md)
