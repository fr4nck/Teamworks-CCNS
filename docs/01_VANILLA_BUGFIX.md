# Teamworks Vanilla — suivi des bugs et correctifs

**Mise à jour : 5 septembre 2026**

## Objectif

Ce fichier recense uniquement les anomalies réellement présentes dans la version originale de Teamworks (`Noethys/Teamworks`) que nous rencontrons ou retrouvons pendant le développement de Teamworks-CCNS.

Objectifs :

1. disposer d'un **Teamworks Vanilla corrigé et utilisable** pendant que Teamworks-CCNS continue son développement ;
2. séparer strictement les bugs historiques des régressions de migration, de la modernisation UI et des extensions CCNS ;
3. préparer des correctifs minimaux éventuellement transmissibles au projet d'origine ;
4. effectuer un **ratissage exhaustif de l'historique du fork et du code Vanilla**, sans confondre candidat et bug confirmé.

## Référence amont

- Projet original : `Noethys/Teamworks`
- Version/base : Teamworks **2.1.3.1**
- Base commune : `00bd52ef85853eb617361a15c2f0cc0cfa1b898e`
- Branche de préparation : `vanilla-bugfix`
- Fork moderne : `fr4nck/Teamworks-CCNS`
- Historique à analyser : environ **1 237 commits** entre la base et le fork moderne.

## Méthode d'audit

L'audit combine deux voies complémentaires :

1. **historique Git** : ratissage des commits ayant corrigé, sécurisé, fiabilisé ou durci un comportement, puis comparaison du diff avec le fichier exact de Teamworks 2.1.3.1 ;
2. **analyse statique du Vanilla** : recherche de familles à risque (`eval`/`exec`, erreurs avalées, index avant garde, chemins absents, getters oubliés, code inaccessible, sauvegarde/restauration, etc.), chaque occurrence restant un simple candidat tant qu'un défaut observable n'est pas démontré.

Un commit `fix` dans Teamworks-CCNS n'est jamais une preuve suffisante. Le défaut doit être présent dans le code Vanilla et indépendant de Python 3/Phoenix, de la nouvelle UI ou des extensions CCNS.

## Premier tri terminé

Le premier audit de 8 familles candidates est terminé. Il a produit les cinq correctifs `VFIX-001` à `VFIX-005` et plusieurs exclusions (Phoenix, UI moderne, régression du fork).

### VFIX-001 — Répertoires de sauvegarde absents

**Fichier :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

Le code original utilise `os.listdir(rep)` sans contrôle préalable. Le backport minimal considère un répertoire absent comme vide et l'ignore lors de la collecte automatique.

**Patch préparé :** `patches/vanilla/VFIX-001-002-sauvegardes.patch`.

### VFIX-002 — Mauvais nombre de lignes dans les grilles de sauvegarde

**Fichier :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

Deux `wx.FlexGridSizer(rows=2, cols=1, ...)` reçoivent réellement trois éléments.

**Patch préparé :** `patches/vanilla/VFIX-001-002-sauvegardes.patch`.

### VFIX-003 — Gadgets : sélection et bornes haut/bas

**Fichier :** `teamworks/Dlg/DLG_Config_gadgets.py`

Le code original peut lire `GetItemData(-1)` avant la garde de sélection et ne protège pas toutes les bornes de déplacement.

**Patch préparé :** `patches/vanilla/VFIX-003-gadgets.patch`.

### VFIX-004 — Aperçu e-mail : navigation hors limites

**Fichier :** `teamworks/Dlg/DLG_Apercu_fusion_emails.py`

La condition d'avance autorise un dépassement du dernier élément et les listes vides / nouveaux indices ne sont pas suffisamment protégés.

**Patch préparé :** `patches/vanilla/VFIX-004-apercu-email.patch`.

### VFIX-005 — Boutons image : ressource absente

**Fichier :** `teamworks/Ctrl/CTRL_Bouton_image.py`

Le contrôle historique ouvre directement la ressource avec PIL et peut casser si le fichier manque ou est illisible.

**Patch préparé :** `patches/vanilla/VFIX-005-boutons-image.patch`.

## Nouveaux défauts confirmés par le ratissage exhaustif

Le ratissage de l'historique complet a commencé après le premier lot. Il démontre déjà que les cinq VFIX initiaux ne constituaient pas l'inventaire complet.

### VFIX-006 — Sauvegarde : faux succès après échec de copie

**Fichier :** `teamworks/Utils/UTILS_Sauvegarde.py`

**Commit de référence côté fork :** `c9974ee94f934f0a4cde4c45e9c0347eab2f76ac`.

Le code Vanilla peut terminer une tentative de copie en échec puis afficher malgré tout le message de réussite. Le correctif doit conditionner le succès final au résultat réel de la copie et conserver l'erreur finale.

**État :** bug Vanilla confirmé ; correction minimale connue ; backport historique à préparer.

### VFIX-007 — Sauvegarde / restauration : gestion d'erreur incohérente

**Fichiers :** `teamworks/Dlg/DLG_Config_sauvegarde.py`, `teamworks/Utils/UTILS_Sauvegarde.py`.

**Commit de référence côté fork :** `181122a7a86c38140c93e3ae14939fedf5805077`.

Plusieurs défauts sont présents dans le Vanilla :

- message d'erreur utilisant `err` alors que la valeur retournée est stockée dans `etat` ;
- gestionnaire `except err:` invalide / dépendant d'un nom qui n'est pas une classe d'exception définie ;
- certains chemins de restauration peuvent annoncer une réussite après un échec ;
- un `dlg.Destroy()` est placé après un `return`, donc inaccessible.

**État :** famille de bugs Vanilla confirmée ; correctif minimal à découper proprement et tester.

### VFIX-008 — Publipostage : enrichissement silencieusement cassé et type de réponse appelé comme une fonction

**Fichier :** `teamworks/Utils/UTILS_Publipostage_donnees.py`.

**Commit de référence côté fork :** `7ed2268065c5fb6eccbb2e69f971efcdf529af8c`.

Deux défauts Vanilla indépendants sont confirmés :

- le bloc d'informations de naissance teste `cp_naiss` alors que la variable n'est pas définie à cet endroit ; un `except` large masque ensuite l'erreur et l'enrichissement disparaît silencieusement ;
- `listeTypesReponses` est une liste mais est appelée comme une fonction dans un test de type, ce qui peut produire un `TypeError`.

**État :** bugs Vanilla confirmés ; backport minimal à préparer sans reprendre les autres évolutions modernes du publiposteur.

### VFIX-009 — Restauration : fichiers temporaires / archives et nom logique

**Fichiers :** `teamworks/Dlg/DLG_Restauration.py`, `teamworks/Utils/UTILS_Sauvegarde.py`.

**Commit de référence côté fork :** `d7491135c5109145d78df336d7115678eda5fd0c`.

Le code original ne garantit pas le nettoyage de certains fichiers déchiffrés temporaires, ne ferme pas explicitement toutes les archives ZIP utilisées pour l'inventaire et reconstruit imparfaitement le nom logique d'une base portant le suffixe `_TDATA`.

**État :** défauts de robustesse Vanilla confirmés ; correctif historique à isoler.

### VFIX-010 — Vacances : validation obligatoire de la période inopérante

**Fichier :** `teamworks/Ol/OL_Vacances.py`.

L'analyse statique du source original a trouvé `if self.ctrl_nom.GetSelection == -1` au lieu de `GetSelection()`. La comparaison porte donc sur l'objet méthode et la garde prévue pour empêcher la validation sans nom de période ne peut pas jouer correctement. Le dialogue peut atteindre `EndModal(wx.ID_OK)` alors qu'aucune période n'est sélectionnée.

Ce défaut est indépendant de Python 3/Phoenix et de nos extensions.

**Patch préparé et vérifié statiquement :** `patches/vanilla/VFIX-010-vacances-selection.patch`.

### VFIX-011 — Frais : intégrité des remboursements et déplacements

**Fichiers :** `teamworks/Dlg/DLG_Saisie_deplacement.py`, `teamworks/Dlg/DLG_Saisie_remboursement.py`, `teamworks/Ctrl/CTRL_Page_frais.py`.

Trois défauts liés sont confirmés dans le code historique :

- `decimal.getcontext().prec = 2` limite tout le contexte Decimal du processus à deux chiffres significatifs ; un calcul tel que `123 × 0,55` peut alors produire `68,00 €` au lieu de `67,65 €` ;
- modifier un déplacement déjà remboursé réécrit systématiquement `IDremboursement=0`, ce qui le détache silencieusement ;
- la sauvegarde d'un remboursement et la mise à jour de ses déplacements sont réalisées dans des écritures/transactions distinctes, tandis que `remboursements.listeIDdeplacement` et `deplacements.IDremboursement` sont lus comme deux représentations concurrentes du même rattachement.

Le correctif côté fork conserve désormais `deplacements.IDremboursement` comme source opérationnelle canonique, garde `listeIDdeplacement` comme projection de compatibilité, traite `NULL` comme l'ancien état non remboursé, et regroupe l'écriture du remboursement avec celle de ses déplacements dans une transaction explicite. La suppression d'un remboursement détache également les déplacements dans le même lot transactionnel.

**État :** bug Vanilla confirmé ; correctif Teamworks-CCNS en qualification sur `fix/frais-integrite-remboursements` ; tests de non-régression SQLite/AST ajoutés. Le backport Vanilla minimal reste à isoler après qualification du correctif moderne.

## Sécurité / durcissement Vanilla — piste séparée

Les faiblesses de sécurité ne doivent pas être mélangées artificiellement avec les bugs fonctionnels. Elles sont suivies comme `VSEC-*` jusqu'à qualification complète.

### VSEC-001 — Sauvegarde / restauration MySQL : exécution et fichier d'identifiants temporaires

**Fichier :** `teamworks/Utils/UTILS_Sauvegarde.py`.

**Commit de référence côté fork :** `1fa4cbdc886a3c0de563a68220f4c9a8357f12b9`.

Le Vanilla utilise notamment un fichier temporaire d'identifiants MySQL sans durcissement explicite des permissions, `subprocess.Popen(..., shell=True, ...)` et une détection de succès qui ne repose pas proprement sur le code retour du processus.

**État :** faiblesse Vanilla confirmée ; portée et backport de sécurité à qualifier séparément avant intégration.

### VSEC-002 — `eval` / `exec` historiques

Plusieurs commits modernes ont remplacé des évaluations littérales ou routages dynamiques historiques (`f05162da`, `544bb369`, `aa90dad4`, `3eb7217f`). Le code Vanilla contient effectivement de nombreuses occurrences `eval`/`exec`, mais chaque occurrence doit encore être examinée : une présence d'`eval` n'est pas à elle seule une vulnérabilité exploitable.

**État :** audit sécurité en cours ; aucun backport massif autorisé sans qualification occurrence par occurrence.

## Analyse statique — première passe ciblée

Une première passe sur les **243 fichiers Python** du snapshot Vanilla a recherché les getters wx utilisés comme objets méthode au lieu d'être appelés.

Quatre occurrences ont été trouvées :

- trois `GetValue` sans parenthèses dans les dialogues de sauvegarde ; dans les chemins étudiés, leur branche de repli produit actuellement le même chemin par défaut et elles restent donc candidates ;
- un `GetSelection` sans parenthèses dans `OL_Vacances.py`, qui neutralise réellement une validation obligatoire : **VFIX-010 confirmé**.

Cette passe ne vaut pas audit statique complet ; d'autres familles sont encore à ratisser.

## Candidat explicitement non confirmé

### Getter `GetValue` sans parenthèses dans le choix de destination

Des occurrences historiques comparent un getter `GetValue` à une chaîne au lieu d'appeler `GetValue()`. La construction est erronée, mais dans les chemins déjà étudiés les deux branches aboutissent au même chemin par défaut lorsque le champ est vide. Elles restent donc **candidates**, pas VFIX confirmés, tant qu'un comportement incorrect distinct n'est pas démontré.

Ce cas illustre la règle : détecté ≠ bug confirmé.

## Éléments sortis du backlog Vanilla

- **Python 3/Phoenix :** parentages `StaticBox` et warnings de flags uniquement révélés/endurcis par Phoenix.
- **Régression de notre fork :** parsing de date corrigé par `416d98b` ; le Vanilla avait déjà la bonne expression.
- **UI/UX moderne :** contrôleurs/listes recrutement après refonte des sections et tokens.

## Validation du premier lot de backports

Les patches `VFIX-001` à `VFIX-005` ont été reconstruits sur une copie exacte du snapshot Vanilla 2.1.3.1 en conservant l'encodage historique `iso-8859-15`.

Validation effectuée :

- `git apply --unidiff-zero --check` : **OK** ;
- application sur copie propre : **OK** ;
- compilation Python via `py_compile` : **OK** ;
- `git diff --check` : **OK**.

`VFIX-010` a également été reproduit sur le fichier historique, corrigé par une modification d'une seule ligne et compilé avec succès ; son patch minimal est conservé séparément.

Il reste le test runtime dans l'environnement historique.

## Mesure d'avancement — deux pourcentages distincts

### 1. Premier lot de cinq correctifs

`VFIX-001` à `VFIX-005` restent à **75 %** chacun : confirmation, solution et patch réalisés ; test runtime historique restant.

Ce pourcentage ne doit plus être présenté comme l'avancement global du chantier Vanilla.

### 2. Audit exhaustif de l'historique et du code

Le ratissage porte sur environ **1 237 commits** et sur une analyse statique complémentaire du source Vanilla. La première tranche d'environ 100 commits a été examinée en profondeur ; la tranche suivante est en cours.

**Avancement indicatif du ratissage historique : environ 8 %.**

À ce stade :

- VFIX fonctionnels confirmés : **11 familles** (`VFIX-001` à `VFIX-011`) ;
- pistes sécurité confirmées / en qualification : **2** (`VSEC-001` et `VSEC-002`) ;
- plusieurs candidats ont déjà été rejetés ou reclassés Phoenix/UI/fork ;
- le nombre final de bugs n'est volontairement pas figé tant que le ratissage n'est pas terminé.

Il serait trompeur de calculer maintenant un « pourcentage de Teamworks Vanilla corrigé » définitif : le dénominateur continue d'augmenter au fur et à mesure de l'audit.

## Principe du futur Teamworks Vanilla corrigé

**Teamworks original + corrections de bugs uniquement.**

Pas de migration Python 3, pas de nouveau thème, pas de CCNS et pas de fonctionnalités supplémentaires.

La branche `vanilla-bugfix` part directement de la base 2.1.3.1 et sert de zone de préparation. Les patches propres restent également conservés dans `patches/vanilla/` afin d'être auditables et transmissibles indépendamment du fork moderne.