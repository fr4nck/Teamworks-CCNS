# Gouvernance Git et rails Teamworks

Date de référence : 2026-09-05

Ce document sauvegarde les règles de travail validées avant nettoyage des conversations. Lorsqu'une information d'état GitHub vieillit, l'état réel du dépôt prévaut. Les règles de gouvernance ci-dessous restent la référence tant qu'elles ne sont pas remplacées explicitement dans Git.

## 1. Rails durables

- `wx/master` = rail wxPython de production et de référence historique.
- `qt/master` = rail durable de migration et d'évolution Qt.
- `master` reste temporairement conservé pour compatibilité avec les workflows, scripts et habitudes historiques, jusqu'à décision explicite de retrait.

## 2. Sens de propagation

- Les corrections métier communes, conformité CCNS, sécurité, compatibilité production et corrections wx nécessaires sont d'abord intégrées côté `wx/master` lorsque leur origine est la production wx.
- Les éléments métier réutilisables sont ensuite propagés de façon contrôlée de `wx/master` vers `qt/master`.
- Les travaux purement UI/runtime Qt ciblent `qt/master`.
- Il n'existe pas de propagation automatique Qt → wx.

## 3. Politique UI

- wxPython reste la référence de production tant que la migration n'est pas achevée.
- On corrige les défauts wx nécessaires ; on évite les grandes refontes UI wx devenues sans intérêt stratégique.
- Les nouveaux développements UI structurants ont vocation à être réalisés en Qt.
- La migration Qt est progressive : écran par écran et domaine par domaine.

## 4. Métier et persistance

- Le rail Qt ne doit pas dupliquer arbitrairement SQL, règles métier ou conventions historiques déjà isolables dans une frontière commune.
- Une règle historique wx n'est pas automatiquement normative : un comportement peut être un bug et doit alors être corrigé ou arbitré avant reproduction.
- Les frontières métier/persistance doivent être pensées pour rester réutilisables par les deux rails lorsque cela est raisonnable.

## 5. Pull requests et intégration

- Aucune PR n'est mergée automatiquement parce que la CI est verte.
- Toute fusion doit être explicitement décidée.
- Les anciennes PR peuvent être fermées sans merge lorsque leur contenu est démontré comme intégré, superseded ou conservé dans une branche de consolidation.
- Les PR de récupération ou de consolidation restent draft tant que leur contenu n'est pas réaligné et requalifié.

## 6. Qualification

Il faut distinguer explicitement :

- CI Linux ;
- CI Windows GitHub ;
- smoke Qt natif qwindows ;
- tests sur base historique versionnée ;
- validation interactive réelle sur poste Windows utilisateur.

Un GO technique automatisé ne vaut pas autorisation de merge ni validation utilisateur terrain.

## 7. Release

- Une qualification Qt réussie ne signifie pas automatiquement qu'un installateur ou une RC Qt est prêt.
- Tant que wx reste le rail de production, une RC de production doit normalement partir de `wx/master`, sauf demande explicite de build de test Qt.
- Les workflows historiques pouvant encore dépendre de `master`, leur cible doit être vérifiée avant toute modification du processus de release.

## 8. Documentation et conversations

- GitHub devient la référence durable : code, tests, docs, issues et PR selon la nature de la décision.
- Une conversation ancienne ne doit pas faire foi contre une décision Git plus récente.
- Toute décision durable prise en conversation doit être matérialisée dans Git avant suppression du chat.
- Les archives de conversations doivent distinguer faits techniques, décisions, hypothèses et états temporaires.

## 9. Portée transverse

Les décisions Teamworks propres au code et à la migration résident dans ce dépôt.

Les décisions transverses concernant Portail, Connecthys, hébergement et infrastructure peuvent également relever de `fr4nck/PMSL-Arch`. Lorsqu'un sujet est transverse, éviter de le redéfinir contradictoirement dans plusieurs dépôts.

## 10. Nettoyage : état vérifié le 12 octobre 2026

Point de comparaison : `wx/master` à
`2abc1d8ddac60b06b33da9536e95edd8135c52ec`.
Les quatre PR ci-dessous sont ouvertes sur GitHub. Cette vérification est
un inventaire de récupération, pas une autorisation de fusion. Les références
distantes ont été actualisées sans suppression ni élagage de branches.

| PR | Sommet source | Constat sur le wx courant | Suite du tri |
| --- | --- | --- | --- |
| [#391](https://github.com/fr4nck/Teamworks-CCNS/pull/391) | `adce8bd09a282b7a339e6bda8c8c010d3162baac` | `scripts/test_windows_installer.ps1` est identique octet pour octet. Le test portable source reste différent et renomme temporairement les dossiers du checkout. | Ne pas réimporter le script historique en bloc. Comparer ses garanties au test actuel `test_windows_portable_isolated.ps1`, qui ne masque pas les sources. Aucun portable ni installateur exécuté pendant cet inventaire. |
| [#452](https://github.com/fr4nck/Teamworks-CCNS/pull/452) | `8edfb4ded5342f3e772ead8715204a5c0b9f9d5a` | Les services `hr_document_workflow`, `mail_merge_data`, `document_template_catalog` et plusieurs modules `domain/documents` sont absents de wx. La branche contient aussi des changements de documentation et de CI. | Récupération métier à examiner par fichiers et dépendances ; aucune intégration globale ni validation Office présumée. |
| [#383](https://github.com/fr4nck/Teamworks-CCNS/pull/383) | `b808c722d3df473619ff519134bc44d0b8a6ce88` | `DLG_Documents_RH.py` et `DLG_Publiposteur_rh.py` sont absents de wx. | Travail UI historique distinct du moteur #452 ; vérifier le besoin et les raccordements avant toute reprise. |
| [#357](https://github.com/fr4nck/Teamworks-CCNS/pull/357) | `6a75377b1d799c4a710c1f6ecf268efd6955be43` | Sommet de consolidation CRH conservé ; 230 commits propres à la source et 584 propres au wx courant depuis leur ancêtre commun. | Préserver les travaux et reprendre domaine, persistance et UI par lots ; ces compteurs ne mesurent pas le nombre de fonctions manquantes. |

La PR [#442](https://github.com/fr4nck/Teamworks-CCNS/pull/442) est déjà fermée
sans fusion depuis le 11 octobre. Sa branche distante a déjà disparu ; le
sommet `5712aa019c557736045b05a214af41b11f579f77` reste disponible sous
`refs/pull/442/head`. L'état ancien « PR et branche ouvertes » est corrigé dans
`docs/03_UI_UX_MODERNISATION.md`. La disparition de cette branche est un constat
antérieur à ce lot, pas une action de nettoyage effectuée ici.

Validation de cet inventaire : 23 tests ciblés réussis sur l'invalidation de
contexte, l'état des vues, les tableaux Personnes et le contrat installateur.
Les parseurs PowerShell ne signalent aucune erreur de syntaxe sur les scripts
installateur et portable isolé actuels. Il s'agit de tests automatisés et de
contrôles statiques, sans nouvelle recette graphique, sans construction ni
exécution du portable et sans validation des quatre sommets historiques.
Qt, `artifacts/`, les fichiers de référence synchronisés et les branches
historiques n'ont pas été modifiés ; aucune PR créée, fermée ou fusionnée.

Suite du tri #391 : l'ancien point d'entrée portable délègue maintenant au
harnais isolé courant. Le test installateur, initialement identique à la
source #391, possède désormais une garde supplémentaire contre `BUILD.txt`
vide. Voir `docs/CI_POLICY.md` pour les garanties conservées, la migration du
rapport et les limites. La PR #391 reste ouverte : le masquage historique du
checkout n'a pas été repris et aucune nouvelle recette EXE n'est déclarée.

## 11. Cible finale à trois branches — décision du 12 octobre 2026

La cible finale confirmée est `master`, `wx/master`, `qt/master`. La décision
historique de conserver temporairement `master` évolue : ce rail reste le socle
commun permanent, comme défini dans les instructions Git actuelles du dépôt.
L'utilisateur exige l'intégration et la validation des corrections avant
suppression. Un tag d'archive seul ne permet donc pas de déclarer un lot terminé.

L'inventaire distant de départ contient 14 branches. Le registre
`docs/audit/branch-preservation-2026-10-12.json` conserve leurs noms et SHA exacts,
les trois rails à garder et les tags annotés des 11 sommets à résorber.
Le sommet de la PR #442 déjà fermée est également conservé.
Les 12 tags ont été publiés et leurs SHA de commits vérifiés sur GitHub.
Une sauvegarde Git complète a été vérifiée, restaurée dans un dépôt séparé,
puis ses 12 sommets comparés aux originaux. Son SHA-256 figure dans le registre.
Les sources non intégrées restent classées `REVIEW`, et non « absorbées ».

Premier lot repris : `ccns/session-actual-hr-inbox`. Les contrats du lot sont
déjà implémentés dans une version plus récente sur les rails ; ses deux fichiers
de tests historiques sont repris sur `wx/master`, avec une seule adaptation
de libellé d'erreur. Les 48 tests historiques/courants/mailbox passent.
Voir `docs/04_CCNS_EXTENSIONS.md` pour le périmètre et les limites exactes.
Après publication de cette preuve, ce sommet peut être retiré avec un contrôle
du SHA distant ; aucun autre lot n'est déclaré supprimable ici.

Résultat réel : la publication de `4bc6244c` sur `wx/master` et la suppression
de `ccns/session-actual-hr-inbox` ont été effectuées dans une seule opération
atomique, sous contrôle des deux SHA distants. Le tag d'archive a été revérifié
après suppression. L'inventaire GitHub compte désormais **13 branches** :
la cible de trois n'est pas encore atteinte. Les dix autres branches historiques
restent à reprendre et qualifier ; les archives n'autorisent pas leur retrait.
