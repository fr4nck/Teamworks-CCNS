# CRH-17B — raccordement « Protection sociale » à la fiche salarié

**État : développement satellite — 1er septembre 2026**

## Objet

CRH-17B raccorde la projection « Protection sociale » au dialogue historique de fiche individuelle sans modifier les parcours RH déjà qualifiés. Le lot reste empilé sur CRH-17A, lui-même fondé sur l'adaptateur de persistance de production CRH-16.

## Comportement

L'onglet **Protection sociale** est ajouté en dernière position du notebook salarié afin de préserver les index des onglets historiques. Il est construit au premier affichage seulement.

Le module de composition RH n'est pas importé lors de l'ouverture de la fiche individuelle : la factory de l'onglet effectue cet import au moment où l'utilisateur ouvre effectivement **Protection sociale**. La lecture utilise alors la composition CRH-17A et, par CRH-16, la base Teamworks active via `GestionDB`.

La première projection est volontairement **en lecture seule**. Elle expose une synthèse descriptive des couvertures, démarches en cours et anomalies ; elle ne calcule ni cotisation ni conformité juridique et n'effectue aucune transmission externe.

## Défaillance isolée

Une erreur du sous-système Connexions RH est interceptée par l'adaptateur runtime de l'onglet. Dans ce cas, l'onglet affiche son indisponibilité mais la fiche individuelle reste utilisable. Cette frontière évite qu'une extension satellite rende indisponibles les parcours historiques salarié, contrats, présences, frais ou recrutement.

## Garde-fous

- aucune migration destructive ;
- aucun changement des tables historiques salarié/contrat ;
- aucun secret ou credential stocké dans l'interface ;
- aucune API ou communication réseau ;
- aucun store SQLite local introduit par le raccordement UI ;
- import du runtime RH différé jusqu'à l'ouverture réelle de l'onglet ;
- tests statiques exécutables sans importer wxPython pour verrouiller la frontière de composition.

## Qualification

CRH-17B est un lot satellite et **ne remplace pas** la validation manuelle Windows de la version 0.9.1b sur copie de base réelle décrite dans `ROADMAP.md` et `docs/VALIDATION_WINDOWS_0.9.1b.md`.

La qualification automatisée de CRH-17B porte uniquement sur sa branche et sa PR empilée. Si ce lot est ultérieurement fusionné jusqu'à `master`, tout nouveau build de pré-release produit depuis ce `master` devra être reconstruit et requalifié conformément à la roadmap.
