# Audit architectural pour l'évolution de Teamworks-CCNS

## Objet et périmètre

Ce document cartographie l'architecture réellement présente dans le dépôt afin de préparer l'évolution long terme de Teamworks-CCNS. Il ne prescrit aucune refonte immédiate, ne modifie aucune règle métier et distingue les constats de code des recommandations progressives.

L'analyse repose sur :

- l'organisation des dossiers Python et des ressources ;
- les imports entre `domain`, `application`, `infrastructure` et `teamworks` ;
- les points d'entrée applicatifs et scripts ;
- les accès base via `teamworks/GestionDB.py` ;
- les écrans wxPython historiques ;
- les modules CCNS ajoutés progressivement ;
- les documents existants de performance, compatibilité, pérennité et maintenance.

## Vue générale

### Architecture actuelle

Le dépôt combine deux architectures de nature différente :

1. un socle historique Teamworks, essentiellement situé dans `teamworks/`, organisé par familles d'écrans wxPython, listes, dialogues, outils et ressources statiques ;
2. une surcouche CCNS plus récente, structurée en couches plus explicites : `domain/`, `application/`, `infrastructure/`, `migrations/`, `teamworks/CcnsCore/` et points d'intégration wxPython.

Vue simplifiée :

```text
Utilisateur wxPython
  ├─ teamworks/Teamworks.py
  ├─ teamworks/Ctrl/*
  ├─ teamworks/Dlg/*
  └─ teamworks/Ol/*
        │
        ├─ teamworks/GestionDB.py
        │    ├─ SQLite local / fichiers .dat .db3
        │    └─ MySQL réseau si configuration réseau
        │
        ├─ teamworks/Utils/* et teamworks/Outils/*
        │
        └─ teamworks/CcnsCore/*
              ├─ audit et synthèses CCNS branchables dans l'interface
              ├─ bridge vers le runtime CCNS moderne
              └─ accès direct à GestionDB pour les données Teamworks réelles

Surcouche CCNS structurée
  ├─ domain/*                 objets métier et règles pures
  ├─ application/*            services applicatifs, bootstrap, sécurité
  ├─ infrastructure/*         dépôts mémoire pour runtime de démonstration/tests
  ├─ migrations/*             schéma SQL cible CCNS
  └─ tests/*                  couverture non graphique et contrats d'intégration
```

### Flux principaux

| Flux | Entrée | Chemin principal | Sortie | Observations |
| --- | --- | --- | --- | --- |
| Lancement graphique Teamworks | `teamworks/Teamworks.py` | wxPython, contrôleurs, dialogues, listes | interface principale | point d'entrée historique, volumineux, fortement couplé à `teamworks/` |
| Accueil CCNS | `teamworks/Ctrl/CTRL_Gadget_CCNS.py` | `teamworks/CcnsCore/home_gadgets_ccns.py` puis audit CCNS | indicateurs d'alerte | chemin déjà optimisé par cache court selon les documents existants |
| Audit contrats CCNS | `teamworks/Dlg/DLG_CCNS_audit.py`, `teamworks/Ol/OL_CCNS_audit.py` | `teamworks/CcnsCore/audit_contracts_ccns.py`, filtres, tri | liste transverse/export | flux métier important, dépend de `GestionDB` et du moteur domaine |
| Dossiers incomplets CCNS | helpers et textes d'intégration dans `teamworks/Dlg` et `teamworks/Ctrl` | `teamworks/CcnsCore/incomplete_files_ccns.py` | synthèse par individu | intégration encore préparatoire par fichiers d'instructions et helpers |
| Runtime CCNS de démonstration/tests | `scripts/demo_runtime.py` | `application/bootstrap/bootstrap_runtime.py`, dépôts mémoire, services applicatifs | données de référence et contrôles | couche saine, testable, mais pas encore persistance réelle complète |
| Génération/export documentaire | dialogues, `teamworks/Utils/UTILS_Publipostage_donnees.py`, documents statiques | modèles `.doc`, `.odt`, `.twd`, exports | fichiers utilisateur | zone historique et transversale, dépendante des chemins, encodages et outils externes |

### Découpage fonctionnel

- **Personnes et candidats** : `teamworks/Ctrl/CTRL_Page_generalites.py`, `teamworks/Ol/OL_personnes.py`, `teamworks/Ol/OL_candidats.py`, `domain/people/`.
- **Contrats** : écrans de création et pages `teamworks/Ctrl/CTRL_Creation_contrat_p*.py`, `teamworks/Ctrl/CTRL_Page_contrats.py`, `teamworks/Ol/OL_contrats.py`, `domain/contracts/`.
- **CCNS conventionnel** : classifications, grilles, minima, règles dans `domain/convention/`, `domain/engine/` et `teamworks/CcnsCore/`.
- **Activité, affectations et planning** : `domain/activity/`, `application/control/assignment_control_service.py`, `teamworks/Ctrl/CTRL_Planning.py`, `teamworks/Ctrl/CTRL_Presences.py`.
- **Sécurité et habilitations** : `domain/security/`, `application/security/` ; intégration graphique encore limitée.
- **Documents, mails et exports** : `teamworks/Utils/`, `teamworks/Outils/mail/`, `teamworks/Dlg/DLG_Publiposteur.py`, ressources `teamworks/Static/Documents/`.
- **Administration et configuration** : nombreux dialogues `teamworks/Dlg/DLG_Config_*.py`, `teamworks/Utils/UTILS_Config.py`, `teamworks/Utils/UTILS_Parametres.py`.

### Découpage technique

| Couche | Dossiers | État architectural |
| --- | --- | --- |
| Domaine pur | `domain/` | dataclasses et règles isolées, peu couplées à l'interface, bonne testabilité |
| Application | `application/` | services minces, bootstrap mémoire, sécurité ; dépend du domaine et des dépôts |
| Infrastructure moderne | `infrastructure/repositories/` | dépôts en mémoire, utiles pour tests/démo, pas encore persistance Teamworks réelle |
| Persistance historique | `teamworks/GestionDB.py`, fichiers `Static/Databases`, migrations | centralise accès SQLite/MySQL, très transversal, dette historique élevée |
| Interface historique | `teamworks/Ctrl/`, `teamworks/Dlg/`, `teamworks/Ol/`, `ObjectListView/` | volumineuse, fortement couplée, responsabilités mélangées UI/données/métier |
| Pont CCNS-Teamworks | `teamworks/CcnsCore/` | zone de raccord pragmatique ; dépend à la fois de `GestionDB`, du domaine et de l'UI |
| Outils transversaux | `teamworks/Utils/`, `teamworks/Outils/` | nombreux services techniques, souvent appelables depuis l'UI, dette variable |
| Documentation et migrations | `docs/`, `migrations/`, `scripts/` | documentation riche ; migrations ordonnées ; scripts limités et utiles aux tests |

## Cartographie des modules

| Composant | Rôle | Responsabilités | Principaux appels | Dépendances | Couplage | Complexité estimée | Fréquence d'utilisation | Importance métier | Facilité de test | Dette estimée |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `domain/common` | base entités | identifiants, horodatage | utilisé par les entités domaine | standard library | faible | faible | permanente indirecte | moyenne | élevée | faible |
| `domain/people` | personnes/profils | données personne et cadre juridique | services et dépôts | `domain/common` | faible | faible | élevée | élevée | élevée | faible |
| `domain/contracts` | contrats | type, régime, organisation, contrat | moteurs de contrôle, dépôts | `domain/common`, enums | faible | faible à moyenne | élevée | très élevée | élevée | faible |
| `domain/convention` | CCNS conventionnel | classifications, grilles, lignes, résolution minima | moteurs minimum et seed | domaine interne | faible | moyenne | élevée pour CCNS | très élevée | élevée | faible à moyenne |
| `domain/engine` | contrôles et anomalies | règles, résultats, anomalies, checks détaillés | `application/control`, `teamworks/CcnsCore/audit_contracts_ccns.py` | contrats, convention | moyen | moyenne | élevée pour audit | très élevée | élevée | moyenne |
| `domain/activity` | activité/affectations | saisons, périodes, lieux, créneaux, affectations | contrôle affectations, dépôts | `domain/common` | faible | faible à moyenne | moyenne | moyenne à élevée | élevée | faible |
| `domain/security` | habilitations | rôles, permissions, utilisateurs, événements sensibles | services sécurité et seed | `domain/common` | faible | faible | encore faible | moyenne | élevée | faible |
| `application/control` | vues et services de contrôle | transformation anomalies/résultats en vues applicatives | domaine engine/contracts/activity | `domain/*` | faible à moyen | faible | moyenne | élevée | élevée | faible |
| `application/bootstrap` | runtime CCNS | création dépôts, seed données référence | dépôts mémoire, seed | `infrastructure`, `domain` | moyen | moyenne | tests/démo | moyenne | élevée | faible |
| `application/security` | règles accès/historique | vérification permissions, journalisation événements sensibles | domaine sécurité | `domain/security` | faible | faible | encore faible | moyenne | élevée | faible |
| `infrastructure/repositories` | dépôts mémoire | stockage générique en mémoire | runtime, tests | domaine | faible | faible | tests/démo | moyenne | élevée | faible |
| `migrations` | schéma cible CCNS | créations de tables CCNS ordonnées | bootstrap futur / installation | SQL | faible | moyenne | installation/évolution | élevée | moyenne | moyenne |
| `teamworks/GestionDB.py` | accès base historique | connexion, requêtes, introspection, migrations, import/export | presque tous les écrans historiques | wx, SQLite/MySQL, chemins | très fort | élevée | permanente | très élevée | faible à moyenne | élevée |
| `teamworks/Teamworks.py` | application graphique | démarrage, fenêtre principale, menus | contrôleurs/dialogues/outils | wx, `teamworks/*` | très fort | élevée | permanente | très élevée | faible | élevée |
| `teamworks/Ctrl` | contrôles/pages wx | pages métier, widgets composés, planning, accueil | `GestionDB`, `Dlg`, `Ol`, `Utils`, `CcnsCore` | wx et modules internes | fort | élevée | permanente | très élevée | faible | élevée |
| `teamworks/Dlg` | dialogues wx | configuration, saisies, assistants, audits, publipostage | `GestionDB`, `Ctrl`, `Ol`, `Utils` | wx, outils externes | fort | élevée | élevée | élevée | faible | élevée |
| `teamworks/Ol` | listes ObjectListView | listes métier, chargement/affichage/export | `GestionDB`, `ObjectListView`, `Utils` | wx/OLV | fort | moyenne à élevée | élevée | élevée | faible | élevée |
| `teamworks/ObjectListView` | widget tiers/local | infrastructure de listes | `teamworks/Ol`, contrôles | wx, six | moyen | élevée | élevée | moyenne | faible | moyenne à élevée |
| `teamworks/Utils` | outils transversaux | config, exports, images, sauvegarde, diagnostic perf, impression | écrans et dialogues | dépendances variées | fort | variable | élevée | moyenne à élevée | variable | élevée |
| `teamworks/Outils/mail` | envoi mail | messages, SMTP, encodage | dialogues mail | standard/email/réseau | moyen | moyenne | ponctuelle | moyenne | moyenne | moyenne |
| `teamworks/CcnsCore` | raccord CCNS réel | audit contrats, synthèses, filtres, tri, seed Teamworks | `GestionDB`, `domain`, `Utils` | mix historique/moderne | moyen à fort | moyenne | élevée pour CCNS | très élevée | moyenne | moyenne |
| `scripts` | démonstrations | runtime CLI non graphique | application bootstrap | application/domain | faible | faible | ponctuelle | faible à moyenne | élevée | faible |
| `tests` | non-régression | tests domaine, services, audit, intégration préparatoire | modules modernes et CCNS | pytest | faible | moyenne | CI/dev | élevée | élevée | faible |
| `teamworks-ccns-individual-summary-files` | artefacts de travail | copies/notes liées à une intégration spécifique | aucun flux principal observé | fichiers isolés | faible | faible | faible | faible | moyenne | moyenne |

## Matrice de criticité

| Composant | Impact métier | Dette technique | Couplage | Priorité | Argument |
| --- | --- | --- | --- | --- | --- |
| `teamworks/GestionDB.py` | très élevé | élevée | très fort | 1 | point central des données, concerné par performance, compatibilité réseau et stabilité ; toute évolution doit être mesurée et progressive |
| `teamworks/CcnsCore/audit_contracts_ccns.py` | très élevé | moyenne | moyen à fort | 1 | calcule la lecture transverse CCNS depuis les données réelles ; composant rentable à stabiliser sans refonte globale |
| `teamworks/Ctrl/CTRL_Page_contrats.py` et assistants contrat | très élevé | élevée | fort | 1 | point naturel de correction métier ; couplage UI/base/référentiels à réduire progressivement |
| `teamworks/Ol/OL_CCNS_audit.py` et `teamworks/Dlg/DLG_CCNS_audit.py` | élevé | moyenne | fort | 2 | affichage de l'audit ; sensible aux volumes et à la testabilité wxPython |
| `domain/engine` | très élevé | moyenne | moyen | 2 | règles métier critiques, mais relativement isolées et testables ; priorité à couvrir davantage avant extensions |
| `domain/convention` | très élevé | faible à moyenne | faible | 2 | cœur CCNS stable ; évolution à sécuriser par tests métier |
| `teamworks/Ctrl/CTRL_Accueil.py` et `CTRL_Gadget_CCNS.py` | élevé | moyenne | fort | 2 | visibilité immédiate utilisateur ; déjà objet d'optimisation locale, éviter les recalculs lourds |
| `teamworks/Ctrl/CTRL_Planning.py` | moyen à élevé | élevée | fort | 3 | fichier volumineux, important mais moins central pour les minima CCNS actuels |
| `teamworks/Dlg/DLG_Publiposteur.py` | moyen | élevée | fort | 3 | très volumineux, génération documentaire et dépendances externes ; modernisation à découper par usage réel |
| `teamworks/ObjectListView` | moyen | moyenne à élevée | moyen | 3 | composant central d'affichage ; remplacement non recommandé sans dossier dédié |
| `application/*` | moyen | faible | faible à moyen | 3 | saine et testable ; priorité à l'utiliser comme point d'extraction plutôt qu'à la refondre |
| `infrastructure/repositories` | moyen | faible | faible | 4 | utile aux tests/démo, pas critique en production tant que la persistance réelle reste dans Teamworks |
| `setup.py` et packaging | moyen | élevée | moyen | 4 | dette de compatibilité déjà identifiée, à traiter dans un lot packaging séparé |

## Cartographie des dépendances

### Dépendances fortes

- `teamworks/Ctrl`, `teamworks/Dlg` et `teamworks/Ol` dépendent fortement de wxPython, de `GestionDB`, des utilitaires et des ressources statiques.
- `teamworks/GestionDB.py` concentre les dépendances vers les moteurs de base, les chemins, wxPython pour les messages et l'instrumentation de performance.
- `teamworks/CcnsCore/audit_contracts_ccns.py` dépend à la fois de `GestionDB` et des objets/règles `domain`, ce qui en fait un pont critique entre legacy et surcouche moderne.
- `application/bootstrap` dépend des dépôts `infrastructure` pour construire un runtime mémoire cohérent.

### Dépendances faibles

- `domain/*` dépend principalement de la bibliothèque standard et de sous-modules domaine.
- `application/control` dépend du domaine mais ne dépend pas de wxPython.
- `scripts/demo_runtime.py` dépend du runtime applicatif sans toucher l'interface.

### Dépendances inutiles ou à vérifier

Aucune dépendance inutile n'a été supprimée dans cet audit. Les zones à vérifier lors de futurs lots sont :

- imports wxPython dans des modules non graphiques historiques ;
- imports globaux de dépendances lourdes dans `teamworks/Utils` alors qu'un import différé pourrait suffire ;
- dossiers d'artefacts `teamworks-ccns-individual-summary-files`, qui semblent être des copies de travail plutôt qu'une couche applicative active.

### Dépendances circulaires

L'analyse statique des imports entre les couches modernes ne met pas en évidence de cycle direct entre `domain`, `application` et `infrastructure` : le sens dominant est `application -> domain`, `infrastructure -> domain`, `application -> infrastructure`, et `teamworks/CcnsCore -> domain/application`.

Dans la zone historique, le risque n'est pas tant un cycle simple qu'un réseau dense d'importations entre `Ctrl`, `Dlg`, `Ol`, `Utils`, `ObjectListView` et `GestionDB`. Ce couplage rend les tests unitaires difficiles et augmente le risque d'effet de bord lors d'un changement local.

### Modules devenus centraux

- `GestionDB` pour les données.
- `teamworks/Utils` pour les fonctions transversales.
- `ObjectListView` et `teamworks/Ol` pour l'affichage de listes.
- `teamworks/CcnsCore/audit_contracts_ccns.py` pour l'audit CCNS réel.
- `domain/engine` pour la logique métier de contrôle.

### Modules à découpler en priorité

1. extraire les lectures CCNS réelles derrière un service de lecture stable ;
2. séparer les transformations métier CCNS des widgets wxPython ;
3. réduire les accès directs `GestionDB` dans les écrans les plus utilisés ;
4. isoler les exports/documentation par interfaces testables ;
5. reporter tout remplacement de `ObjectListView` tant que les usages et volumes ne sont pas mesurés.

## Zones stables

- **Entités `domain`** : fichiers courts, responsabilités limitées, peu dépendants du reste du dépôt. Ils ne devraient être modifiés que pour une évolution métier explicitement couverte par tests.
- **Services `application/control` et `application/security`** : services minces, non graphiques, testables. Ils sont adaptés à une extension progressive.
- **Dépôts mémoire `infrastructure/repositories`** : simples et utiles au runtime de démonstration ; ne pas les complexifier pour remplacer prématurément la persistance réelle.
- **Migrations CCNS existantes** : constituent une base ordonnée ; à compléter par migrations incrémentales plutôt qu'à réécrire.
- **Instrumentation `UTILS_Diagnostic_performance`** : déjà désactivée par défaut, conforme au cadre de performance ; à conserver comme outil d'observation.

## Zones fragiles

- **Interface wxPython historique** : fichiers très longs, logique UI mêlée aux accès base et à la transformation métier. Les tests automatisés y sont difficiles.
- **`GestionDB`** : composant central, ancien, fortement sollicité, avec responsabilités multiples : connexion, exécution SQL, introspection, migration, import/export et compatibilité SQLite/MySQL.
- **Listes et ObjectListView** : potentiel de chargements complets, reconstructions de listes et blocages du thread graphique.
- **Génération documentaire/publipostage** : beaucoup de formats, dépendances externes, chemins et modèles statiques ; risque élevé de régression utilisateur.
- **Ponts CCNS dans `teamworks/CcnsCore`** : utiles et pragmatiques, mais ils concentrent l'adaptation entre modèle moderne et base réelle historique.
- **Packaging** : `setup.py` et dépendances binaires reflètent des hypothèses historiques déjà signalées dans la matrice de compatibilité.

## Opportunités de modernisation

| Ordre | Type | Proposition | Bénéfice attendu | Risques | Effort estimé |
| --- | --- | --- | --- | --- | --- |
| 1 | amélioration locale | mesurer systématiquement les chemins audit, accueil, fiches contrat et listes avant modification | décisions factuelles, cohérence avec la politique performance | mesures non représentatives si base trop petite | faible |
| 2 | extraction d'un service | créer un service de lecture CCNS réel au-dessus de `GestionDB` pour contrats/classifications/grilles | réduit duplication SQL, prépare tests et cache local | erreur de mapping si couverture insuffisante | moyen |
| 3 | découplage | déplacer transformations audit/synthèse hors widgets wxPython | tests non graphiques plus simples, UI plus légère | adaptation progressive des écrans | moyen |
| 4 | amélioration locale | prioriser les fichiers avec `SELECT *`, `fetchall()` et listes non bornées sur les écrans fréquents | gains ciblés sans changer l'architecture | ne pas casser colonnes attendues implicitement | moyen |
| 5 | découplage | isoler exports et génération documentaire derrière fonctions testables | réduit risque sur formats et encodage | tests de fichiers plus lourds | moyen à élevé |
| 6 | remplacement progressif | remplacer certains assistants/dialogues volumineux par sous-composants internes, écran par écran | lisibilité et testabilité | risque UX si trop large | élevé |
| 7 | refonte structurelle ciblée | envisager seulement après mesures un remplacement de la stratégie de listes ou d'accès base | bénéfice potentiel sur performance/compatibilité | coût et risque élevés, forte surface utilisateur | très élevé |

Modernisations non recommandées à court terme :

- réécriture globale de Teamworks ;
- connexion globale permanente à la base sans mesures réseau/concurrence ;
- remplacement massif de wxPython ;
- remplacement global d'ObjectListView ;
- gel arbitraire ou mise à jour massive des dépendances sans matrice de tests.

## Analyse de la maintenabilité

### Fichiers très longs observés

Les fichiers Python les plus longs sont notamment :

| Fichier | Lignes approximatives | Risque principal |
| --- | ---: | --- |
| `teamworks/ObjectListView/ObjectListView.py` | 4349 | composant central et complexe, probablement issu d'un composant tiers/local |
| `teamworks/Dlg/DLG_Publiposteur.py` | 3061 | génération documentaire volumineuse |
| `teamworks/ObjectListView/ListCtrlPrinter.py` | 3027 | impression/listes, dépendances UI |
| `teamworks/Ctrl/CTRL_Planning.py` | 2931 | planning complexe, rendu wxPython |
| `teamworks/Utils/UTILS_ListCtrlPrinter.py` | 2880 | impression/export transversal |
| `teamworks/Ctrl/CTRL_thumbnailctrl.py` | 2294 | widget spécialisé images/vignettes |
| `teamworks/Dlg/DLG_Statistiques.py` | 2119 | statistiques et UI mélangées |
| `teamworks/Teamworks.py` | 1876 | démarrage/application principale |
| `teamworks/Dlg/DLG_Scenario.py` | 1836 | scénario, UI et logique |
| `teamworks/Ctrl/CTRL_Page_generalites.py` | 1723 | fiche personne, données et UI |
| `teamworks/FonctionsPerso.py` | 1418 | utilitaires historiques transversaux |
| `teamworks/GestionDB.py` | 1319 | persistance centrale |

### Fonctions longues et responsabilités multiples

Cet audit n'a pas réécrit les fonctions longues. Les zones à analyser en priorité par lots sont :

- méthodes de chargement/sauvegarde dans les écrans de contrats, personnes, planning et publipostage ;
- méthodes de remplissage de listes ObjectListView ;
- fonctions de `GestionDB` qui combinent construction SQL, exécution, conversion et affichage d'erreur ;
- fonctions d'export et impression qui mélangent sélection utilisateur, formatage et écriture fichier.

### Duplications importantes

- ouvertures répétées de `GestionDB.DB()` dans de nombreux écrans ;
- requêtes SQL construites localement dans les dialogues/listes ;
- patterns wxPython de chargement, validation, message d'erreur et rafraîchissement répétés ;
- logique de référentiels probablement répétée dans les configurations et fiches ;
- intégrations CCNS parfois décrites par fichiers texte en attente de branchement effectif.

### Dépendances cachées

- chemins et ressources sous `teamworks/Static` ;
- variables de configuration et fichiers utilisateur ;
- disponibilité de wxPython et dépendances natives ;
- comportement SQLite/MySQL selon configuration locale ou réseau ;
- imports historiques parfois relatifs au répertoire courant de lancement.

### Points de fragilité

- base réseau et verrouillage concurrent ;
- rendu graphique en bureau distant ;
- packaging Windows/Python historique ;
- imports de dépendances spécifiques plateforme ;
- encodage et casse des chemins entre Windows, Linux et macOS ;
- absence de tests graphiques automatisés pour les écrans historiques.

## Compatibilité avec la feuille de route existante

### Convergences

- L'audit architectural confirme les priorités de l'audit de performances : accès base, listes volumineuses, référentiels, planning, rendu wxPython et stratégie de connexion.
- La recommandation d'un service partagé CCNS rejoint la feuille de route de maintenance : mutualiser les lectures CCNS sans refonte globale.
- Les risques packaging/dépendances recoupent la matrice de compatibilité : wxPython, OpenCV, Pillow, MySQL, chemins et Python moderne.
- La politique de pérennité est cohérente avec l'approche proposée : changements sobres, mesurés, documentés et réversibles.

### Contradictions éventuelles

Aucune contradiction forte n'a été constatée. La seule tension est opérationnelle : le README mentionne encore une installation Python 3.7+, alors que la matrice rappelle que les évolutions doivent viser des versions récentes et maintenues. Cela ne bloque pas l'audit architectural, mais doit rester un lot de compatibilité dédié.

### Nouveaux risques identifiés

- Les artefacts `teamworks-ccns-individual-summary-files` peuvent créer de la confusion s'ils sont considérés comme code actif.
- Le pont `teamworks/CcnsCore` devient central : il doit rester lisible et couvert par tests pour éviter de recréer une couche legacy parallèle.
- Les documents d'intégration `.txt` dans `teamworks/Dlg` et `teamworks/Ctrl` doivent être remplacés progressivement par branchements vérifiés ou archivés comme notes, afin de clarifier l'état réel.

## Vision long terme

### Phase 1 : corrections locales et observation

- Collecter des mesures sur base représentative pour accueil, audit, fiches contrat/personne, listes et planning.
- Compléter les tests non graphiques autour des règles CCNS déjà présentes.
- Clarifier les artefacts de travail et documents d'intégration non exécutés.
- Ne modifier que les requêtes ou transformations dont le gain et le risque sont documentés.

### Phase 2 : découplages ciblés

- Introduire un service de lecture CCNS réel au-dessus de `GestionDB`.
- Déplacer les transformations audit/synthèse dans des fonctions testables hors wxPython.
- Stabiliser les contrats de données entre audit, gadgets, dossiers incomplets et fiche individuelle.
- Réduire progressivement les accès directs aux référentiels dans les écrans les plus fréquents.

### Phase 3 : modernisation progressive

- Extraire des sous-composants pour les dialogues volumineux lorsque des modifications fonctionnelles les touchent déjà.
- Isoler exports, impression et publipostage derrière des fonctions testées.
- Traiter packaging et dépendances par lots compatibles avec Windows, Linux, macOS Intel/ARM et versions Python maintenues.
- Étendre les migrations CCNS sans modifier rétroactivement les migrations déjà appliquées.

### Phase 4 : refontes ciblées éventuelles

- Décider d'une refonte d'un composant seulement si les mesures, la couverture métier et le plan de retour arrière sont disponibles.
- Candidats possibles : stratégie d'accès base pour certaines unités de travail, listes volumineuses, génération documentaire, packaging.
- Ne pas engager de réécriture globale : la coexistence entre historique Teamworks et surcouche CCNS reste le chemin le moins risqué.

## Conclusion

Teamworks-CCNS possède une base moderne CCNS relativement saine (`domain`, `application`, `infrastructure`) raccordée à un socle Teamworks historique très riche mais fortement couplé. La modernisation la plus rentable n'est pas une refonte générale : elle consiste à consolider les ponts CCNS, extraire les lectures et transformations testables, mesurer les chemins utilisateurs réels et découpler progressivement les écrans les plus critiques.
