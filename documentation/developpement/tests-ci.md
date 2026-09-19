# Tests et CI

## Tests

Plusieurs centaines de fichiers `tests/test_*.py`. Grands thèmes récurrents (comptage approximatif par préfixe de nom) : contrôle salarial/CCNS des contrats (dominant), recrutement, audit CCNS, fiche individuelle (« généralités »), migrations Phoenix/UI, salaire, planning/mission/employé, et des tests de « contrat d'interface » pour les dialogues secondaires, exécutés spécifiquement dans le job Windows.

## CI : un seul workflow (`.github/workflows/ci.yml`)

!!! warning "Politique du dépôt : un seul fichier de workflow"
    Le dépôt impose volontairement un unique fichier `.github/workflows/ci.yml` (« aucun workflow parallèle ou auto-modifiant », voir `docs/CI_POLICY.md`). Toute évolution de l'intégration continue — y compris pour la documentation — passe par un job supplémentaire dans ce même fichier, jamais par un nouveau fichier de workflow.

Quatre jobs réels :

1. **cleanup-actions** (Windows) — nettoyage périodique de l'historique GitHub Actions, sur planification ou déclenchement manuel.
2. **tests** (Ubuntu) — compilation Python complète, audits statiques (risques runtime, branches Phoenix redondantes), puis `pytest`.
3. **windows-smokes** (Windows) — tests de contrat des dialogues et parcours smoke réels (sauvegarde/restauration, contrat, exports, impression, navigation, présence, recrutement) plus un aller-retour base fonctionnelle.
4. **build-windows** (Windows) — construit le paquet portable avec **PyInstaller** et l'installateur Inno Setup, uniquement sur tag de version, déclenchement manuel, ou commit `master` contenant `[windows]`. Publie une Release GitHub le cas échéant.

Politique résumée (`docs/CI_POLICY.md`) : preuve utile sans surcoût, aucun build Windows automatique sur PR/push, un seul workflow Windows, annulation des runs concurrents, **aucun build déclenché pour une modification documentaire seule**.

### Où s'insère la documentation

Un job `docs` dédié, ajouté dans ce même `ci.yml`, construit `mkdocs build --strict` sur les pull requests qui touchent `documentation/`, `mkdocs.yml` ou `requirements/docs.txt`, et publie sur GitHub Pages uniquement sur push vers `master` — sans jamais déclencher le job Windows. Voir [Contribuer et documenter](contribuer.md).

## Voir aussi

[Démarrer en développement](demarrer-dev.md) · [Packaging et releases](packaging-releases.md) · [Organisation du dépôt](organisation-depot.md)
