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
- TW-180 : suppression des doubles checkboxes Phoenix.

### Lots actifs après TW-180

- **TW-181 — Nettoyage du packaging Windows** : PR #253 ouverte. Les tests du socle et les parcours critiques Windows sont verts. Le build portable doit encore être exécuté explicitement sur cette branche afin de vérifier la disparition des warnings liés aux anciennes versions d’actions GitHub et aux collectes PyInstaller trop larges avant fusion.
- **TW-182 — Branding Teamworks CCNS et personnalisation association** : branche `agent/tw-182-branding-teamworks-ccns` active. Le développement peut avancer en parallèle, mais sa fusion ne doit pas court-circuiter la séquence de stabilisation et de validation Windows.

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

- PR #253 ouverte pour TW-181 ;
- branche `agent/tw-182-branding-teamworks-ccns` ouverte pour TW-182 ;
- aucune issue ouverte, les Issues étant désactivées sur le dépôt ;
- `master` reste la seule base de référence ;
- le dernier lot fonctionnel fusionné est TW-180 ;
- les branches de travail doivent partir de `master` et rester isolées par objectif ;
- les anciennes branches peuvent rester comme historique, mais ne doivent pas piloter les décisions de développement.

## 5. Priorité immédiate — validation réelle avant pré-release

La stabilisation Windows reste prioritaire. Les développements non bloquants peuvent avancer sur des branches isolées, mais aucune nouvelle fonction métier, convention collective ou refonte visuelle importante ne doit être fusionnée au détriment des validations suivantes :

1. valider TW-181 par un build portable Windows de sa branche ;
2. fusionner TW-181 si le packaging est propre et fonctionnel ;
3. produire un portable Windows depuis le `master` courant ;
4. vérifier le démarrage et les smoke tests automatisés sur ce build ;
5. exécuter le parcours minimal sur une copie de base réelle ;
6. corriger uniquement les anomalies bloquantes réellement constatées ;
7. documenter les résultats ;
8. décider ensuite seulement si la version mérite une qualification bêta ou RC.

TW-182 peut être développé en parallèle afin de ne pas bloquer l’avancement, mais son intégration finale doit préserver cette discipline de stabilisation.

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
- statistiques ;
- vérification des écrans à checkboxes ;
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

TW-181 vise à réduire le bruit de packaging sans modifier le runtime métier : actions GitHub compatibles Node 24 et retrait des collectes PyInstaller globales inutiles de wxPython et Matplotlib. Le build portable de validation doit notamment confirmer que le backend Matplotlib `wxagg` et les statistiques restent disponibles.

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

## 9. Thèmes, branding et affichage

Le mode `Système` doit reprendre les couleurs natives exposées par wxWidgets. Les modes `Clair` et `Sombre` restent des surcharges explicites.

Le code de préférences, de persistance, de restauration et de thème natif est intégré. La validation manuelle doit encore confirmer sur les écrans prioritaires :

- lisibilité complète ;
- absence de panneaux incohérents ;
- absence de texte tronqué avec l’échelle choisie ;
- persistance après redémarrage ;
- comportement correct des sélections et états désactivés.

### TW-182 — identité visuelle Teamworks CCNS

Le branding cible devient explicitement **Teamworks CCNS** afin de distinguer le fork spécialisé CCNS du logiciel historique.

Périmètre prévu :

- nouveau logo Teamworks CCNS moderne, lisible et exploitable en petite taille ;
- suppression/remplacement des anciens visuels Teamworks datés utilisés au splash, à l’accueil ou comme fond ;
- splash cohérent en thème clair et sombre ;
- barre de chargement centrée ;
- logo de l’association utilisatrice affiché sous la zone de chargement ;
- crédit discret `© Teamworks CCNS` en pied de splash, sans année codée en dur ;
- possibilité de définir un logo d’association dans les paramètres ;
- conservation automatique des proportions, sans étirement ;
- PNG transparent recommandé, JPEG accepté ;
- fallback automatique vers le branding Teamworks CCNS si aucun logo d’association n’est défini ou si le fichier est invalide ;
- stockage de la personnalisation utilisateur hors des assets statiques afin qu’une mise à jour ne l’écrase pas ;
- identité Teamworks CCNS conservée pour l’icône de l’application ;
- intégration du logo de l’association dans l’accueil sans remplacer l’identité du logiciel ;
- réutilisation du même logo d’organisation dans les en-têtes des PDF, impressions et autres documents imprimables, à la manière de Noethys ;
- absence de duplication du fichier logo : tous les documents doivent utiliser la source de branding centrale, avec fallback propre si aucun logo n’est configuré ;
- cohérence complète des deux thèmes clair et sombre.

Les maquettes servent de référence visuelle, mais l’implémentation finale doit respecter les contraintes wxPython, le packaging Windows et les réglages existants.

## 10. Données, encodages, dates et compatibilité

État consolidé :

- sources et ressources textuelles suivies migrées vers UTF-8 ;
- compatibilité avec certains anciens encodages conservée aux frontières d’import ;
- normalisation centrale des dates historiques ;
- suppression des découpages manuels de dates recensés ;
- champs masqués de dates fiabilisés ;
- connexion MySQL/MariaDB historique maintenue sans migration du serveur ;
- aucune migration destructive de la base réalisée dans ces lots.

Toute future migration de données devra rester séparée, sauvegardée et réversible.

## 11. Dette technique encore autorisée

Les audits de dette technique restent des outils de prévention, pas des prétextes à lancer des nettoyages massifs avant la validation Windows.