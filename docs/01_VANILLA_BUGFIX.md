# Teamworks Vanilla — suivi des bugs et correctifs

**Mise à jour : 25 août 2026**

## Objectif

Ce fichier recense uniquement les anomalies réellement présentes dans la version originale de Teamworks (`Noethys/Teamworks`) que nous avons rencontrées ou mises en évidence pendant le développement de Teamworks-CCNS.

Objectifs :

1. disposer d'un **Teamworks Vanilla corrigé et utilisable** pendant que Teamworks-CCNS continue son développement ;
2. séparer strictement les bugs historiques des régressions de migration, de la modernisation UI et des extensions CCNS ;
3. préparer des correctifs minimaux éventuellement transmissibles au projet d'origine.

## Référence amont

- Projet original : `Noethys/Teamworks`
- Version/base : Teamworks **2.1.3.1**
- Base commune : `00bd52ef85853eb617361a15c2f0cc0cfa1b898e`
- Branche de préparation : `vanilla-bugfix`
- Fork moderne : `fr4nck/Teamworks-CCNS`

## Résultat du premier tri

L'audit des **8 familles candidates initiales est terminé**.

| Famille initiale | Classement | Conclusion |
|---|---|---|
| Parentage `StaticBox` / contrôles | Python 3 / Phoenix | Les corrections rencontrées correspondent au comportement plus strict de Phoenix ; pas de backport Vanilla sans preuve dans l'environnement historique. |
| Sizers / layouts | Mixte | Les warnings de flags sont plutôt Phoenix ; les deux grilles de sauvegarde à 2 lignes recevant 3 éléments sont un vrai bug Vanilla. |
| Parsing des dates personne | Régression du fork | Vanilla contient bien `datetime.date(annee, mois, jour)` ; la mauvaise expression avait été introduite puis corrigée chez nous. |
| Sauvegardes / sources absentes | Vanilla | `os.listdir(rep)` est appelé sans vérifier que le répertoire existe. |
| Gadgets / absence de sélection | Vanilla | Lecture de `GetItemData(-1)` et déplacements non bornés. |
| Aperçu e-mail / navigation | Vanilla | Condition d'avance décalée et indices/liste vide insuffisamment protégés. |
| Listes / contrôleurs recrutement | UI/UX moderne | Les correctifs concernent notre architecture refondue, pas le code Vanilla. |
| Icônes / ressources absentes | Vanilla — robustesse | Le bouton historique ouvre directement la ressource et peut casser si elle manque ou est illisible. |

## Backlog Vanilla confirmé

### VFIX-001 — Répertoires de sauvegarde absents

**Fichier :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

Le code original utilise `os.listdir(rep)` sans contrôle préalable. Le backport minimal considère un répertoire absent comme vide et l'ignore lors de la collecte automatique.

**Patch préparé :** `patches/vanilla/VFIX-001-002-sauvegardes.patch`.

### VFIX-002 — Mauvais nombre de lignes dans les grilles de sauvegarde

**Fichier :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

Deux `wx.FlexGridSizer(rows=2, cols=1, ...)` reçoivent réellement trois éléments. Les deux déclarations concernées passent à `rows=3` ; la grille à deux éléments reste volontairement inchangée.

**Patch préparé :** `patches/vanilla/VFIX-001-002-sauvegardes.patch`.

### VFIX-003 — Gadgets : sélection et bornes haut/bas

**Fichier :** `teamworks/Dlg/DLG_Config_gadgets.py`

Le backport vérifie la sélection avant `GetItemData`, interdit le déplacement au-delà du premier/dernier élément et protège `OnItemSelected` contre un index invalide.

**Patch préparé :** `patches/vanilla/VFIX-003-gadgets.patch`.

### VFIX-004 — Aperçu e-mail : navigation hors limites

**Fichier :** `teamworks/Dlg/DLG_Apercu_fusion_emails.py`

Le backport protège les listes vides, borne l'avance au dernier élément et vérifie le nouvel index avant sélection.

**Patch préparé :** `patches/vanilla/VFIX-004-apercu-email.patch`.

### VFIX-005 — Boutons image : ressource absente

**Fichier :** `teamworks/Ctrl/CTRL_Bouton_image.py`

Le backport reste compatible avec le Python historique : pas de `pathlib`, pas de design system. Il protège `None`/chaîne vide, vérifie `os.path.isfile` et tolère `IOError`/`OSError` lors de l'ouverture de l'image.

**Patch préparé :** `patches/vanilla/VFIX-005-boutons-image.patch`.

## Validation du backport préparé

Les quatre fichiers ont été reconstruits sur une **copie exacte du snapshot Vanilla 2.1.3.1**, en conservant l'encodage historique `iso-8859-15`.

Validation effectuée :

- `git apply --unidiff-zero --check` : **OK** pour les quatre patches ;
- application des quatre patches sur une copie propre : **OK** ;
- compilation Python des quatre fichiers modifiés via `py_compile` : **OK** ;
- `git diff --check` : **OK**.

Cette validation est statique. Il reste à exécuter Teamworks dans son environnement historique et à parcourir réellement sauvegarde/restauration, gadgets, aperçu e-mail et boutons avec ressource absente.

Le format patch à contexte nul est volontaire : il permet de préserver l'encodage historique sans convertir tout le fichier en UTF-8 et sans polluer le diff avec des dizaines de changements artificiels.

## Éléments sortis du backlog Vanilla

- **Python 3/Phoenix :** parentages `StaticBox` et warnings de flags uniquement révélés/endurcis par Phoenix.
- **Régression de notre fork :** parsing de date corrigé par `416d98b`.
- **UI/UX moderne :** contrôleurs/listes recrutement après refonte des sections et tokens.

## Mesure d'avancement

Chaque correctif vaut 4 étapes :

1. bug confirmé dans Vanilla ;
2. correction minimale identifiée ;
3. backport construit et applicable sur le socle Vanilla ;
4. test runtime dans l'environnement historique.

| Correctif | Confirmé | Solution connue | Backport préparé | Runtime Vanilla | Avancement |
|---|---:|---:|---:|---:|---:|
| VFIX-001 Sauvegarde / dossier absent | Oui | Oui | Oui | Non | 75 % |
| VFIX-002 Grilles sauvegarde | Oui | Oui | Oui | Non | 75 % |
| VFIX-003 Gadgets | Oui | Oui | Oui | Non | 75 % |
| VFIX-004 Aperçu e-mail | Oui | Oui | Oui | Non | 75 % |
| VFIX-005 Icônes absentes | Oui | Oui | Oui | Non | 75 % |

**Progression du lot Vanilla connu : 75 %.**

Le dernier quart correspond au test réel du logiciel historique, pas à davantage de développement théorique.

## Principe du futur Teamworks Vanilla corrigé

**Teamworks original + corrections de bugs uniquement.**

Pas de migration Python 3, pas de nouveau thème, pas de CCNS et pas de fonctionnalités supplémentaires.

La branche `vanilla-bugfix` part directement de la base 2.1.3.1 et sert de zone de préparation jusqu'à création éventuelle d'un dépôt/fork dédié. Les patches propres restent également conservés dans `patches/vanilla/` afin d'être auditables et transmissibles indépendamment du fork moderne.
