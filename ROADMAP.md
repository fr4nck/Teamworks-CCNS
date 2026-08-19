# Teamworks-CCNS — Roadmap officielle et unique

**Mise à jour : 19 août 2026**

Ce fichier est l’unique roadmap de référence du projet. Toute autre documentation peut détailler un domaine, mais ne doit pas porter une roadmap concurrente ni annoncer un niveau de maturité différent.

## 1. État réel du projet

Teamworks-CCNS est actuellement en **`0.9.0-dev`**.

Le socle Python 3 / wxPython Phoenix, la CI et le packaging Windows sont largement stabilisés. Le dépôt sait construire un portable Windows reproductible, exécuter des parcours critiques Windows automatisés et publier une Release sur tag conforme.

La qualification **bêta / RC / stable reste volontairement refusée** tant que le parcours Windows minimal n’a pas été validé manuellement sur une copie de base réelle par l’utilisateur.

Aucune CI verte, aucun pourcentage d’avancement et aucun ZIP généré ne suffisent à qualifier une version.

## 2. Règles de vérité

Chaque annonce doit distinguer explicitement :

- code modifié ;
- tests automatisés réussis ;
- exécutable construit ;
- parcours Windows réellement exécuté ;
- validation utilisateur obtenue.

Les formulations « presque fini » et les dates de sortie non démontrées sont interdites.

## 3. Historique consolidé

Les lots TW historiques ont été traités par PR successives. La quasi-totalité des PR récentes est fusionnée dans `master`.

### Stabilisation et runtime intégrés

- TW-136 à TW-143 : dates, Unicode, UTF-8, workflow unique, filtres recrutement, sélection multiple et exports ;
- TW-144 à TW-147 : audits wx/Python et inventaire des bare-excepts RH ;
- TW-149 à TW-170 : extraction en lots ciblés des gardes runtime initialement regroupés dans l’audit TW-139 ;
- TW-171 : compatibilité MySQL/MariaDB 5.5 et diagnostic du portable Windows ;
- TW-172 : recherche phonétique des villes ;
- TW-173 : publiposteur sous wxPython 4.3 ;
- TW-174 : alignement du runtime Windows sur wxPython 4.3.1 ;
- TW-175 : horaires à la minute ;
- TW-176 : stabilisation du planning sous wxPython 4.3 ;
- TW-177 : lanceur diagnostic ;
- TW-178 : nettoyage des légendes de présence ;
- TW-179 : robustesse des champs de contrat ;
- TW-180 : suppression des doubles checkboxes Phoenix ;
- TW-181 : nettoyage des warnings du packaging Windows et validation du portable allégé.

### Lots actifs ou réservés

- **TW-182 — Branding Teamworks CCNS** : PR #254 ouverte en draft. Branding, logo d’organisation et profil structure sont implémentés ; fusion bloquée jusqu’au contrôle visuel clair/sombre et au test du portable.
- **TW-183 — Architecture planning** : identifiant réservé au moteur de planning/remplacement. La spécification peut être documentée, mais aucun autre lot ne doit réutiliser cet identifiant.
- **TW-184 — Moteur de contrats piloté par convention** : PR #255 ouverte en draft. Le lot sépare convention, type de contrat, classification, qualification/statut et rémunération ; CCNS et CEE sont le premier périmètre raccordé. La rétrocompatibilité des contrats historiques reste obligatoire.

### PR d’audit historique #209

La PR #209 « TW-139 — Auditer et stabiliser les parcours runtime » a servi de chantier d’exploration et d’audit global. Son contenu utile a ensuite été extrait en lots ciblés, testés et fusionnés individuellement dans `master` (notamment TW-149 à TW-170, puis les corrections runtime suivantes).

**La PR #209 est fermée comme supersédée depuis le 19 août 2026 et ne doit plus être utilisée comme branche de travail ni comme prérequis de merge.**

La PR technique #251, créée uniquement pour tester une remise à niveau de cette ancienne branche, a également été fermée sans fusion.

### Collisions historiques d’identifiants TW

Plusieurs identifiants ont été réutilisés dans l’historique avant la consolidation de la gouvernance documentaire, notamment `TW-087`, `TW-088`, `TW-117`, `TW-123`, `TW-126`, `TW-138` et `TW-139`.

Ces collisions sont conservées comme faits historiques et ne doivent pas être réécrites artificiellement.

**Un identifiant `TW-*` déjà présent dans une branche, un commit, une issue ou une PR ne doit plus être réattribué.**

## 4. État GitHub au 19 août 2026

État courant :

- `master` reste la base de vérité ;
- TW-181 est fusionné dans `master` ;
- PR #254 / TW-182 est ouverte en draft ;
- PR #255 / TW-184 est ouverte en draft ;
- TW-183 est réservé au planning et ne correspond pas à une branche active ;
- les anciennes branches peuvent rester comme historique, mais ne doivent pas piloter les décisions de développement.

Les PR draft ne sont pas considérées comme intégrées tant qu’elles ne sont pas fusionnées dans `master`.

## 5. Priorité immédiate — stabiliser les lots actifs puis valider réellement

Les lots déjà engagés TW-182 et TW-184 peuvent être menés jusqu’à un état testable, mais aucune nouvelle refonte fonctionnelle indépendante ne doit les contourner.

Priorité :

1. maintenir la CI Linux et les parcours critiques Windows verts sur les PR actives ;
2. terminer TW-184 sans migration destructive et avec lecture des contrats historiques ;
3. conserver TW-182 en draft jusqu’au contrôle visuel réel ;
4. produire ensuite un portable Windows depuis le `master` retenu ;
5. exécuter le parcours minimal sur une copie de base réelle ;
6. corriger uniquement les anomalies bloquantes réellement constatées ;
7. décider ensuite seulement si la version mérite une qualification bêta ou RC.

## 6. Parcours minimal de validation Windows

Un build n’est qualifiable en pré-release que si le parcours suivant est entièrement validé depuis un dossier fraîchement décompressé, sans dépendre d’un environnement développeur :

- lancement de `Teamworks-CCNS.exe` ;
- ouverture d’une copie de base réelle ;
- affichage de l’accueil ;
- affichage de la liste des salariés ;
- ouverture d’une fiche salarié ;
- ouverture de chaque onglet ;
- modification d’une donnée de test ;
- enregistrement ;
- fermeture et redémarrage ;
- vérification de la persistance ;
- création d’une sauvegarde ;
- restauration d’une copie ;
- contrats / DUE ;
- présences ;
- recrutement ;
- frais ;
- paramètres ;
- rapports / publipostage / impression ;
- fermeture sans processus résiduel.

Chaque étape doit avoir un résultat daté et préciser sa nature : automatique, CI Windows, test manuel développeur ou validation utilisateur.

## 7. Packaging Windows — état actuel

Le workflow unique `.github/workflows/ci.yml` construit le paquet Windows uniquement :

- sur déclenchement manuel explicite avec l’option de build ;
- sur tag `v*`.

Le packaging est fondé sur Python 3.11, Windows Server 2022 et PyInstaller. Le runtime Windows automatisé utilise désormais wxPython 4.3.1.

Le build :

- inventorie les modules internes ;
- inclut les paquets chargés dynamiquement ;
- inclut ressources et fichiers de version essentiels ;
- exécute un smoke test de démarrage ;
- produit un manifeste UTF-8 ;
- vérifie les empreintes SHA-256 des fichiers ;
- produit la somme SHA-256 du ZIP ;
- conserve la liste des dépendances réellement utilisées ;
- publie une GitHub Release uniquement lorsqu’un tag correspond exactement à `VERSION`.

TW-181 a supprimé les collectes PyInstaller globales inutiles de wx et Matplotlib et modernisé les actions GitHub, sans modifier le métier.

Ce niveau de packaging est une condition nécessaire mais non suffisante pour une RC.

## 8. CI — état actuel

La CI doit rester **unique, lisible et frugale**.

Le seul workflow autorisé est `.github/workflows/ci.yml`.

Il regroupe :

- compilation et audits sur Ubuntu 24.04 / Python 3.11 ;
- politique UTF-8 ;
- tests automatisés ;
- parcours critiques Windows ;
- contrôles des checklists Phoenix ;
- dialogues critiques (personne, présence, recrutement, contrat) ;
- aller-retour fonctionnel sur base de test ;
- build portable uniquement sur demande explicite ou tag.

Aucun deuxième workflow ne doit être ajouté pour contourner ou dupliquer ces contrôles.

## 9. Thèmes et affichage

Le mode `Système` doit reprendre les couleurs natives exposées par wxWidgets. Les modes `Clair` et `Sombre` restent des surcharges explicites.

Le code de préférences, de persistance, de restauration et de thème natif est intégré. TW-182 complète ce socle par le branding Teamworks CCNS et le logo d’organisation, mais reste en draft jusqu’à validation visuelle.

La validation manuelle doit encore confirmer sur les écrans prioritaires :

- lisibilité complète ;
- absence de panneaux incohérents ;
- absence de texte tronqué avec l’échelle choisie ;
- persistance après redémarrage ;
- comportement correct des sélections et états désactivés.

## 10. Données, encodages, dates et compatibilité

État consolidé :

- sources et ressources textuelles suivies migrées vers UTF-8 ;
- compatibilité avec certains anciens encodages conservée aux frontières d’import ;
- normalisation centrale des dates historiques ;
- suppression des découpages manuels de dates recensés ;
- champs masqués de dates fiabilisés ;
- connexion MySQL/MariaDB historique maintenue sans migration du serveur ;
- aucune migration destructive de la base réalisée dans ces lots.

Toute future migration de données devra rester séparée, sauvegardée et réversible. Les évolutions de schéma TW-184 doivent rester additives et idempotentes.

## 11. Dette technique encore autorisée

Les audits de dette technique restent des outils de prévention, pas des prétextes à lancer des nettoyages massifs avant la validation Windows.

Restent notamment à suivre :

- bare-excepts RH inventoriés par TW-147 ;
- avertissements wxWidgets non bloquants encore visibles dans certains `StaticBoxSizer` ;
- dette Phoenix résiduelle hors parcours critique ;
- validations multiplateformes non prioritaires par rapport au poste Windows cible.

Ces sujets ne bloquent une pré-release que s’ils provoquent une anomalie réelle sur le parcours minimal.

## 12. Socle RH neutre après stabilisation

Après validation du parcours minimal :

- personnes ;
- contrats ;
- classifications ;
- absences ;
- congés ;
- plannings ;
- pointage ;
- documents ;
- droits ;
- historique ;
- sauvegardes ;
- exports.

Chaque bloc doit rester utilisable indépendamment des conventions collectives.

## 13. Moteur réglementaire

Les règles ne doivent pas être dispersées dans les écrans. Chaque règle doit comporter au minimum :

- identifiant stable ;
- domaine ;
- source ;
- date d’effet ;
- population concernée ;
- paramètres ;
- méthode de calcul ;
- message utilisateur ;
- cas limites ;
- tests associés ;
- historique de version.

Une règle n’est jamais déclarée prise en charge sans cas de tests démontrés.

TW-184 doit respecter cette architecture : l’interface consomme les règles de domaine et ne devient pas la source des minima, classifications ou barèmes.

## 14. Périmètre CCNS PMSL après stabilisation

Ordre de consolidation métier :

1. groupes et classifications ;
2. minima conventionnels et historique des grilles ;
3. temps partiels ;
4. ancienneté ;
5. préparation et trajets ;
6. durée du travail et dépassements ;
7. congés et absences ;
8. arrêts maladie et accidents du travail ;
9. apprentis et alternants ;
10. CEE ;
11. stagiaires ;
12. services civiques ;
13. salariés mineurs.

## 15. Intégrations après stabilisation

- imports CSV ou Excel ;
- rapprochement Noethys ;
- exports paie et comptabilité ;
- Dolibarr ;
- rapports PDF ;
- tableau de bord ;
- interface web ;
- autres conventions collectives.

Aucune intégration ne doit fragiliser le socle local.

## 16. Critères de maturité

### Bêta interne

- parcours minimal Windows validé ;
- aucune perte de données connue ;
- sauvegarde et restauration validées ;
- erreurs bloquantes journalisées ;
- fonctions annoncées réellement accessibles.

### Release candidate

- bêta utilisée sur copie réelle ;
- anomalies bloquantes corrigées ;
- tests de non-régression exécutés ;
- packaging reproductible ;
- validation explicite de l’utilisateur.

### Version stable

- période d’utilisation réelle sans anomalie bloquante ;
- procédure de secours documentée ;
- données récupérables ;
- règles métier critiques sourcées et testées ;
- limites connues publiées.

## 17. Mode de développement continu

- un seul fichier de roadmap : `ROADMAP.md` ;
- `master` comme vérité courante ;
- pas de ZIP à chaque PR ;
- workflow GitHub Actions unique ;
- PR regroupées par objectif testable ;
- aucune fusion sans critère de sortie explicite ;
- changelog fondé sur des fonctions vérifiées ;
- priorité aux parcours complets plutôt qu’au nombre de commits ;
- aucun nouvel identifiant TW sans vérification préalable de son absence dans l’historique ;
- les lots déjà absorbés ou supersédés sont fermés et ne sont pas réactivés artificiellement ;
- après une instruction générale de poursuite, les étapes techniques sûres peuvent être enchaînées sans demander une validation à chaque micro-étape ; seules les décisions métier, les conflits ambigus et les opérations risquées nécessitent un arrêt explicite.

## 18. Prochain jalon

Le prochain jalon est **la stabilisation des PR actives, puis la validation Windows réelle du `master` retenu**.

Séquence :

**TW-184 CI + smoke Windows → contrôle du parcours contrat/publipostage → maintien de TW-182 en draft jusqu’au contrôle visuel → fusion des lots validés → build portable `master` → parcours minimal sur copie réelle → correction des seuls blocages → décision de qualification pré-release.**
