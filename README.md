# Teamworks-CCNS

Fork de **Teamworks** orienté **CCNS** pour la gestion d’équipes, de contrats, de classifications et de contrôles métier dans le sport associatif.

Projet d’origine : Teamworks.

> **Statut actuel : `0.9.0-dev`.** Le dépôt n’est pas encore qualifié bêta, RC ou stable. Une qualification de pré-release exige encore la validation manuelle du parcours Windows minimal sur une copie de base réelle.

## Positionnement

Teamworks-CCNS n’est pas une réécriture complète de Teamworks. Le projet conserve le socle historique utile, le migre progressivement vers Python 3 / wxPython Phoenix et ajoute une couche métier CCNS raccordée aux écrans existants.

Les points d’entrée principaux restent :

- l’accueil et ses alertes ;
- la fenêtre **Dossiers incomplets** pour la supervision ;
- la **fiche individuelle** pour la lecture détaillée ;
- les écrans **contrats** pour les corrections ;
- l’**audit CCNS** pour la vue transverse et les exports.

## État technique consolidé

Le dépôt a désormais franchi plusieurs étapes importantes :

- migration Python 3 / wxPython Phoenix largement consolidée ;
- socle historique converti en UTF-8 ;
- normalisation centrale des dates et suppression des découpages manuels fragiles ;
- préférences d’affichage Système / Clair / Sombre et échelle de police ;
- thème Système basé sur les couleurs natives exposées par wxWidgets ;
- diagnostic de premier démarrage et préflight SQLite en lecture seule ;
- packaging Windows portable reproductible avec manifeste et sommes SHA-256 ;
- publication automatique des builds de version lors d’un tag conforme à `VERSION` ;
- workflow GitHub Actions unique ;
- tests Linux et parcours critiques Windows regroupés dans ce workflow ;
- corrections récentes des listes, sélections multiples et boîtes d’export.

La référence de planification est **uniquement `ROADMAP.md`**. Les autres documents détaillent un domaine mais ne doivent pas porter de roadmap concurrente.

## Couche métier CCNS

Le fork contient notamment :

- personnes et profils juridiques ;
- contrats ;
- classifications CCNS ;
- grilles salariales ;
- affectations ;
- règles métier et résultats de contrôle ;
- anomalies et compteurs individuels ;
- audit CCNS et listes exportables ;
- synthèse CCNS par individu.

Une première couche moderne de lecture des données CCNS est introduite au-dessus de `GestionDB` :

- `domain/repositories/ccns_data.py` définit les DTO de lecture ;
- `infrastructure/persistence/ccns_data_reader.py` centralise les requêtes SQL pour les contrats, classifications, grilles et lignes de grilles ;
- `teamworks/CcnsCore/audit_contracts_ccns.py` consomme ce lecteur.

Cette couche prépare une migration progressive sans modifier le comportement utilisateur ni imposer une refonte brutale de `GestionDB`.

## Environnement actuellement validé par la CI

La CI de référence utilise :

- **Python 3.11** ;
- **Ubuntu 24.04** pour les tests et audits du socle ;
- **Windows Server 2022** pour les parcours critiques wxPython et le packaging ;
- `pytest==8.4.1` et `six==1.17.0` pour le job de tests ;
- `PyInstaller==6.16.0` pour le build Windows.

Cela ne signifie pas que toutes les plateformes ou versions de Python sont qualifiées. La matrice réelle se trouve dans `docs/MATRICE_COMPATIBILITE.md`.

## Installation et lancement depuis les sources

Pour le développement courant, utiliser **Python 3.11**, version actuellement exercée par la CI.

```bash
python -m pip install -r requirements.txt
cd teamworks
python Teamworks.py
```

Les anciennes mentions « Python 3.7 ou plus » ne constituent plus une cible supportée.

## Paquet Windows portable

Le build Windows est volontairement coûteux et n’est pas lancé automatiquement pour chaque modification. Il est déclenché :

- manuellement via le workflow unique avec l’option de build Windows ;
- automatiquement lors d’un tag `v*` conforme au contenu de `VERSION`.

Le paquet vérifie notamment :

- la présence des modules internes inventoriés ;
- les ressources essentielles ;
- le démarrage de l’exécutable ;
- un manifeste UTF-8 des fichiers ;
- les empreintes SHA-256 du contenu et de l’archive ;
- la liste des dépendances utilisées pour le build.

Un ZIP construit avec succès n’est toutefois **pas** à lui seul une RC.

## Validation avant pré-release

Le prochain jalon est un parcours Windows manuel complet depuis un dossier fraîchement décompressé, sur une copie de base réelle :

1. lancer l’exécutable ;
2. ouvrir la base ;
3. afficher l’accueil et la liste des salariés ;
4. ouvrir une fiche individuelle et tous ses onglets ;
5. modifier une donnée de test, enregistrer et relire ;
6. vérifier sauvegarde et restauration sur copie ;
7. fermer proprement sans processus résiduel.

La qualification bêta/RC ne sera posée qu’après preuve de ce parcours conformément à `ROADMAP.md`.

## CI et frugalité

Le dépôt impose un seul fichier de workflow : `.github/workflows/ci.yml`.

La politique est volontairement frugale :

- un job Linux automatique pour compilation, audits et suite de tests ;
- des parcours critiques Windows regroupés ;
- aucun workflow parallèle ou auto-modifiant ;
- build du portable uniquement sur demande explicite ou tag de version ;
- diagnostics conservés brièvement lorsque cela suffit.

## Documentation de référence

- `ROADMAP.md` — **roadmap officielle et unique** ;
- `AGENTS.md` — règles opérationnelles pour les agents et contributeurs ;
- `docs/MATRICE_COMPATIBILITE.md` — état réel des environnements et plateformes ;
- `docs/CI_POLICY.md` — politique CI ;
- `docs/35-perennite-technique.md` — règles de pérennité et dépendances ;
- `docs/30-cartographie-teamworks-ccns.md` — cartographie fonctionnelle et technique ;
- `docs/40-couche-acces-donnees.md` — couche moderne d’accès aux données CCNS ;
- `docs/FEUILLE_ROUTE_MAINTENANCE.md` — priorités de maintenance, sans roadmap concurrente.

## Principe directeur

> **Pas de surcouche décorative : une surcouche métier CCNS utile, progressive, testable et branchée sur les écrans réellement utilisés.**
