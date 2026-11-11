# Teamworks-CCNS — Roadmap officielle et unique

**Mise à jour : 11 novembre 2026**

Ce fichier est l’unique roadmap de référence du projet. Toute autre documentation peut détailler un domaine, mais ne doit pas porter une roadmap concurrente ni annoncer un niveau de maturité différent.

Les décisions d’architecture transverses, le partage des responsabilités entre applications et les priorités interapplications sont définis dans **`fr4nck/PMSL-Arch`**. `ROADMAP.md` reste l’unique roadmap d’exécution propre à Teamworks-CCNS : elle traduit ces décisions en lots d’implémentation, tests, packaging et qualification du produit.

En cas de divergence sur l’architecture ou les flux entre Teamworks, Noethys, Connecthys/Portail, PMSL Équipe ou un service externe, **PMSL-Arch fait foi**. En cas de divergence sur l’état d’implémentation, la maturité ou la qualification de Teamworks-CCNS, **le présent fichier fait foi**. Les priorités interapplications ne doivent donc pas être redéfinies ici sous la forme d’une roadmap concurrente.

## Décision active — gel fonctionnel du rail wx 0.9.2 (11 novembre 2026)

**Statut : gel fonctionnel wx ACTIF, réversible sur décision explicite.** Objectif : terminer la recette et, si les critères sont acquis, publier `v0.9.2` stable. Cette décision ne signifie ni « logiciel sans bug », ni arrêt de la maintenance.

- **Périmètre gelé :** `wx/master` ; pas de nouveau module, nouvelle fonctionnalité métier, refonte globale de l'interface, changement de schéma ou chantier d'architecture non indispensable avant la stable.
- **Travaux autorisés :** correction d'anomalies réelles et reproduites, sécurité, exactitude CCNS, intégrité des données, sauvegarde/restauration, accessibilité d'un parcours existant réellement bloqué, tests, CI, packaging, documentation et recette.
- **Exception possible :** le responsable du projet peut lever ponctuellement le gel pour un besoin justifié. Consigner avant le changement : motif, portée, impact métier et SQL, risques, preuves attendues, plan de retour arrière et décision explicite. Requalifier intégralement le périmètre touché ; publier un nouveau jalon si le code change, **sans réécrire RC12**.
- **Branches :** `master`, `wx/master`, `qt/master` demeurent les trois branches permanentes ; aucune propagation automatique entre rails. Le chantier Qt n'est pas soumis à ce gel wx.

### Release de référence : `v0.9.2-rc12`

- [Préversion RC12 publiée le 11 novembre 2026](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12) : tag sur `9b02fbe94016b403255eabdaa856176d7f3e0ac5`, ZIP portable, installateur x64 et fichier SHA-256.
- [CI qualifiante `42675793471`](https://github.com/fr4nck/Teamworks-CCNS/actions/runs/42675793471) : 2 902 tests PASS, 12 SKIP ; parcours Windows et packaging réussis, provenance et sommes vérifiées.
- **Essai utilisateur acquis :** lancement du portable RC12 sur Windows 11 / 5700X et reprise des paramètres de connexion de l'espace de travail.
- **Non acquis :** recette métier de bout en bout sur **copie de données**, persistance et restauration, compatibilité Word/Writer, DPI 125/150 %, parcours complet du Mailer et comportement en réseau réel contrôlé. L'essai de démarrage sur le profil habituel n'est pas assimilé à une recette isolée ; aucune modification de données de production n'est présumée sûre.

### TW-UI-01 — état du chantier Mailer

Les corrections SMTP/Mailjet et de progression wx sont incluses dans RC12. Les bancs natifs Windows sur transport fictif sont PASS ; les scénarios de réseau réel et la validation interactive de l'application complète restent ouverts. Les preuves historiques sont conservées dans [Phase 3](docs/TW-UI-01-MAILER-PHASE3.md) et le [protocole RC12 mis à jour](docs/TW-UI-01-RECETTE-CANDIDAT-RC12.md). Les anciens constats « RC non publiée » décrivaient **l'état au 9 novembre**, avant publication, et ne sont plus le statut courant.


## 1. État réel du projet

La version publiée du rail wx est **`0.9.2-rc12` (préversion)**. `VERSION` identifie ce candidat ; **`v0.9.2` stable n'existe pas encore**. Le commit de la release est `9b02fbe9` ; les commits documentaires ultérieurs sur `wx/master` ne changent ni cet exécutable ni son tag.

Le socle Python 3 / wxPython Phoenix, la CI et le packaging Windows sont avancés et qualifiés automatiquement. Le démarrage Windows de RC12 a été confirmé par l'utilisateur, sans recette RH complète. Le gel fonctionnel ci-dessus est une **décision d'organisation révisable**, pas une déclaration de maturité stable.

Les jalons `0.9.1b`, CI #789 et PR #314 cités dans les sections historiques suivantes sont conservés pour la traçabilité ; ils ne décrivent **pas** la version wx actuellement publiée.


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
- TW-181 : nettoyage des avertissements et du packaging Windows ;
- TW-182 : branding Teamworks CCNS, organisation, références administratives RH et comportement du thème Système Windows, intégré sélectivement après TW-189 ;
- TW-184 : moteur de contrats, règles CCNS/CEE, schéma additif, modèles, opérations de contrat, publipostage et gardes métier, intégré sélectivement après TW-189 ;
- TW-186 : libellés des dossiers incomplets clarifiés ;
- TW-187 : diagnostics de crash transmissibles ;
- TW-188 : boîte noire technique et détection des freezes ;
- TW-189 : fondations UI modernes, thème et apparence séparés, échelle d’interface globale, navigation et layouts flexibles, modernisation progressive des écrans et découpage de plusieurs contrôleurs historiques.

### Durcissements post-intégration

Avant fusion de #268, les parcours critiques ont aussi été durcis sur des défauts runtime réels :

- une copie finale de sauvegarde en échec ne peut plus être annoncée comme réussie ;
- le publipostage tolère les dossiers incomplets, références pays absentes et sélections vides sans faux succès ni plantage ;
- la restauration nettoie le fichier déchiffré temporaire, ferme les archives d’inventaire et restitue correctement le nom logique sans suffixe `_TDATA` parasite ;
- les rapports d’audit runtime générés par la CI ne sont plus versionnés dans le dépôt.

### PR d’audit historique #209

La PR #209 « TW-139 — Auditer et stabiliser les parcours runtime » a servi de chantier d’exploration et d’audit global. Son contenu utile a ensuite été extrait en lots ciblés, testés et fusionnés individuellement dans `master`.

**La PR #209 est fermée comme supersédée depuis le 19 août 2026 et ne doit plus être utilisée comme branche de travail ni comme prérequis de merge.**

La PR technique #251, créée uniquement pour tester une remise à niveau de cette ancienne branche, a également été fermée sans fusion.

### Collisions historiques d’identifiants TW

Plusieurs identifiants ont été réutilisés dans l’historique avant la consolidation de la gouvernance documentaire, notamment `TW-087`, `TW-088`, `TW-117`, `TW-123`, `TW-126`, `TW-138` et `TW-139`.

Ces collisions sont conservées comme faits historiques et ne doivent pas être réécrites artificiellement.

**Un identifiant `TW-*` déjà présent dans une branche, un commit, une issue ou une PR ne doit plus être réattribué.**

## 4. État GitHub au 31 août 2026

État de référence :

- `master` est la vérité courante ;
- la PR #265 a fusionné TW-189 dans `master`, commit d’intégration `91dfb6d` ;
- la PR #268 a consolidé les deltas encore utiles de TW-182/TW-184, commit d’intégration `8074a1a` ;
- la PR #314 a corrigé la garde de non-régression devenue obsolète après l’extraction de `DLG_Fiche_individuelle_core.py` ;
- la PR #314 a été fusionnée par le commit **`4a226af71facf4fe201e022086e6dd00a46ecbf0`** ;
- la qualification automatisée de ce commit est la CI **#789** ;
- les tests du socle, les parcours critiques Windows et le job de packaging Windows de la CI #789 sont tous réussis ;
- l’artefact `Teamworks-CCNS-Windows` a été produit depuis ce même commit ;
- aucune Release GitHub n’a été publiée : le run n’était pas déclenché par un tag de version ;
- les anciennes branches peuvent rester comme historique, mais ne doivent pas piloter les décisions de développement ;
- la PR #270 reste un profil de compatibilité MySQL 5.5 isolé et n’est pas un prérequis de qualification du produit courant.

## 5. Priorité immédiate — recette finale sur copie avant `v0.9.2` stable

**Acquis :** RC12 publiée et traçable ; tests Linux/Windows, packaging, manifestes et démarrage sur poste utilisateur validés. **Pas encore acquis :** validation fonctionnelle exhaustive et sauvegarde/restauration sur copie indépendante.

Priorités, sans ajout de fonctionnalités :

1. Préparer une copie autorisée des données (ou jeu de recette représentatif), distincte de la base utilisée en exploitation, et une restauration de secours.
2. Vérifier les écrans RH : salariés, neuf onglets, contrats CDI/CDD/CEE, renouvellement/avenants, présence, recrutement, frais, préférences et persistance après redémarrage.
3. Éprouver sauvegarde **et** restauration sur la copie, sans altérer la base de production.
4. Vérifier documents Word/Writer, classement, publipostage, impression et rendu Windows à 100/125/150 %.
5. Tester le Mailer complet sur transport fictif/local contrôlé, sans courriel réel ; conserver comme non qualifiés les scénarios SMTP/Mailjet réels non exercés et préciser si cela limite la stable.
6. Relever résultats datés, anomalie reproductible, gravité, correction éventuelle et requalification du nouvel exécutable si le code change.
7. Appliquer les critères de maturité de la section 16 avant de décider de publier `v0.9.2` stable.

Le protocole courant est [TW-UI-01 / recette RC12](docs/TW-UI-01-RECETTE-CANDIDAT-RC12.md). La fiche `VALIDATION_WINDOWS_0.9.1b.md` reste un document d'archive et ne doit pas être complétée comme si elle qualifiait RC12.


## 6. Parcours minimal de validation Windows

Avant d'envisager `v0.9.2` stable, le parcours suivant doit être entièrement validé sur un exécutable qualifié, une copie de données et sans dépendre d'un environnement développeur :

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
- création d’un contrat CCNS moderne ;
- création d’un contrat CEE ;
- renouvellement CDD / transformation CDD vers CDI lorsque le jeu de données le permet ;
- modèle de contrat et publipostage / impression ;
- présences ;
- recrutement ;
- frais ;
- paramètres, organisation et références administratives RH ;
- rapports / publipostage / impression ;
- fermeture sans processus résiduel.

Chaque étape doit avoir un résultat daté et préciser sa nature : automatique, CI Windows, test machine sur exécutable ou validation utilisateur.

## 7. Packaging Windows — état actuel

Le workflow unique `.github/workflows/ci.yml` construit le paquet Windows uniquement sur demande explicite :

- déclenchement manuel avec l’option de build ;
- tag `v*` conforme à `VERSION` ;
- commit `master` ou `wx/master` explicitement marqué `[windows]` pour une construction technique contrôlée.

Il n’existe donc pas de génération systématique d’un paquet à chaque push ou à chaque PR.

Le job portable dépend maintenant des tests Linux et, hors tag, des parcours critiques Windows. L’ancienne exception de build liée à la branche TW-189 a été supprimée.

Le packaging est fondé sur Python 3.11, Windows Server 2022 et PyInstaller. Le runtime Windows automatisé utilise wxPython 4.3.1.

Le build :

- inventorie les modules internes ;
- inclut les paquets chargés dynamiquement ;
- inclut ressources et fichiers de version essentiels ;
- exécute un smoke test de démarrage de l’exécutable ;
- produit un manifeste d’intégrité du paquet ;
- vérifie les empreintes SHA-256 des fichiers ;
- produit la somme SHA-256 du ZIP ;
- conserve la liste des dépendances réellement utilisées ;
- écrit `BUILD.txt` avec le SHA de construction ;
- publie une GitHub Release uniquement lorsqu’un tag correspond exactement à `VERSION`.

Ce niveau de packaging est une condition nécessaire mais non suffisante pour une RC.

## 8. CI — référence courante et historique

La CI doit rester **unique, lisible et frugale**.

**Référence wx RC12 (9 novembre 2026) :** run `42675793471`, commit `9b02fbe9` : 2 902 PASS, 12 SKIP, parcours critiques Windows et paquets portables/installables PASS. Ce run construit les binaires publiés le 11 novembre. Les informations ci-dessous sur CI #789 constituent un jalon historique du socle `0.9.1b`, pas la dernière CI de RC12.

Le seul workflow autorisé est `.github/workflows/ci.yml`.

Il regroupe :

- compilation et audits sur Ubuntu 24.04 / Python 3.11 ;
- politique UTF-8 ;
- tests automatisés ;
- refus de tout chemin SQLite binaire avec plafond **0** ;
- parcours critiques Windows ;
- contrôles des checklists Phoenix ;
- dialogues critiques (personne, présence, recrutement, contrat) ;
- sauvegarde / restauration ;
- exports et impression PDF ;
- aller-retour fonctionnel sur base de test ;
- build portable et installateur uniquement sur demande explicite, marqueur `[windows]` sur `master` ou tag ;
- nettoyage contrôlé de l’historique GitHub Actions sur déclenchement manuel.

Qualification historique `0.9.1b`, CI **#789**, commit `4a226af71facf4fe201e022086e6dd00a46ecbf0` :

- **1 893 tests pytest réussis, 3 ignorés** ;
- **332/332 fichiers Python de l’inventaire compilables** ;
- **0/0 chemin SQLite binaire** ;
- tous les contrôles du socle réussis ;
- tous les parcours critiques Windows réussis ;
- construction du portable réussie ;
- contrôle du contenu du paquet réussi ;
- démarrage automatisé de l’exécutable réussi ;
- manifeste d’intégrité réussi ;
- archive portable créée ;
- installateur Windows créé ;
- artefact Windows publié par GitHub Actions ;
- Release GitHub volontairement non publiée hors tag.

Les anciennes qualifications, dont #463 et #571, restent des jalons historiques mais ne décrivent plus l’état courant du `master`.

Aucun deuxième workflow ne doit être ajouté pour contourner ou dupliquer ces contrôles.

## 9. Thèmes, affichage et branding

Le mode `Système` suit le système d’exploitation. Sous Windows, le moteur consulte notamment la préférence `AppsUseLightTheme`. Les modes `Clair` et `Sombre` restent des surcharges explicites.

Le socle consolidé comprend :

- un moteur de thème central ;
- des rôles de couleurs sémantiques ;
- la séparation accent / apparence ;
- une échelle unique de l’interface de 80 % à 200 % ;
- la conservation de `echelle_police` uniquement comme compatibilité de migration ;
- la mise à l’échelle conjointe des textes, icônes et métriques de contrôles ;
- des layouts plus flexibles ;
- une navigation principale modernisée ;
- des composants et helpers typographiques communs ;
- le branding Teamworks CCNS ;
- un logo d’organisation configurable ;
- les écrans Structure / association et Références administratives RH accessibles depuis les préférences ;
- des gardes de non-régression sur le thème Système Windows et les assets de branding.

Le cycle d’import Windows `UTILS_Traduction -> UTILS_Fichiers -> UTILS_Customize -> UTILS_Theme -> UTILS_Interface -> UTILS_Traduction` découvert pendant la consolidation TW-189 reste supprimé et verrouillé par test.

La validation manuelle doit encore confirmer sur les écrans prioritaires :

- lisibilité complète ;
- absence de panneaux incohérents ;
- absence de texte tronqué avec l’échelle choisie ;
- persistance après redémarrage ;
- comportement correct du mode Système en clair et sombre ;
- comportement correct des sélections et états désactivés ;
- affichage du branding et du logo d’organisation ;
- absence de réapparition des anciens problèmes de grands espaces, séparateurs rigides ou doubles contrôles.

## 10. Données, contrats et compatibilité

État consolidé :

- sources et ressources textuelles suivies en UTF-8 ;
- compatibilité avec certains anciens encodages conservée aux frontières d’import ;
- normalisation centrale des dates historiques ;
- champs masqués de dates fiabilisés ;
- connexion MySQL/MariaDB historique maintenue sans migration du serveur ;
- schéma du moteur de contrats ajouté de manière additive, compatible avec MariaDB 5.5 ;
- aucune migration destructive de la base réalisée dans ces lots ;
- contrats historiques, CCNS modernes et CEE disposent de chemins de lecture / affichage et de publipostage dédiés ;
- les règles de création, période d’essai, opérations CDD, préflights et contrôles de rémunération disposent de tests dédiés.

Toute future migration de données devra rester séparée, sauvegardée et réversible.

## 11. Dette technique encore autorisée

Les audits de dette technique restent des outils de prévention, pas des prétextes à lancer des nettoyages massifs avant la validation Windows.

Restent notamment à suivre :

- bare-excepts historiques hors parcours critiques ;
- dette Phoenix résiduelle hors parcours critique ;
- avertissements wxWidgets non bloquants ;
- validations multiplateformes non prioritaires par rapport au poste Windows cible.

L’audit pré-RC à haute confiance exécuté pendant la consolidation post-TW-189 a rendu **0 bloqueur**. L’inventaire large de dette n’est pas assimilé à un échec de qualification.

Ces sujets ne bloquent une pré-release que s’ils provoquent une anomalie réelle sur le parcours minimal ou enfreignent un gate automatisé explicite.

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

## 18. Prochain jalon — sortie du gel vers la stable wx

**Prochain jalon : terminer la recette Windows RC12 sur copie de données**, corriger les seuls défauts confirmés, puis décider de `v0.9.2` stable en appliquant la section 16. Le paquet de référence reste la [RC12 publiée](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12), run `42675793471`, commit `9b02fbe9`.

Une correction de code exige un **nouveau commit**, ses régressions et une nouvelle qualification du paquet ; ne jamais déplacer ou reconstruire silencieusement le tag `v0.9.2-rc12`. Une dérogation au gel est possible **uniquement sur décision explicite et tracée**, selon la décision active en tête de ce fichier.

La sortie du gel se décide séparément de la publication stable. Elle n'est ni automatique ni conditionnée par une simple absence de ticket GitHub.

