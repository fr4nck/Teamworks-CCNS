# Audit de caractérisation — Scénarios et Frais wxPython

## Cadre

- Référence auditée : `fr4nck/Teamworks-CCNS`, branche `master`, commit `fd88dbf6025db22f9340c9eefed8c3df09ca8c3b`.
- Périmètre : Scénarios, Déplacements, Remboursements, listes de gestion et impression des frais.
- Hors périmètre respecté : aucun changement sous `poc/qt-theme/`, aucune réécriture d'écran, aucun SQL Qt, aucun refactoring du code historique.
- Modifications du lot : tests de caractérisation statique/exécutable et présent rapport uniquement. Aucun fichier de production n'est modifié.

Les écrans historiques ouvrent des boîtes wxPython et des connexions de base dès leur initialisation. Les tests ajoutés analysent donc leur AST sans importer wxPython. Deux méthodes suffisamment pures sont aussi extraites de l'AST et exécutées avec des doublures minimales.

## Modèle de données réellement impliqué

| Table | Colonnes utiles au périmètre | Observation |
|---|---|---|
| `scenarios` | `IDscenario`, `IDpersonne`, `nom`, `description`, `mode_heure`, `detail_mois`, `date_debut`, `date_fin`, `toutes_categories` | En-tête d'un scénario. |
| `scenarios_cat` | `IDscenario_cat`, `IDscenario`, `IDcategorie`, `prevision`, `report`, `date_debut_realise`, `date_fin_realise` | Une ligne par catégorie scénarisée ; le report est une chaîne typée. |
| `cat_presences` | `IDcategorie`, `nom_categorie`, `IDcat_parent`, `ordre`, `couleur` | Référentiel des catégories affichées dans les scénarios. |
| `presences` | `IDpersonne`, `IDcategorie`, `date`, `heure_debut`, `heure_fin` | Source du réalisé et des catégories utilisées sur la période. |
| `distances` | `IDdistance`, départ, arrivée, `distance` | Cache symétrique d'une distance d'aller simple. |
| `deplacements` | identité/personne/date/trajet, `distance`, `aller_retour`, `tarif_km`, `IDremboursement` | Porte le rattachement opérationnel au remboursement. Aucun montant n'est stocké. |
| `remboursements` | `IDremboursement`, `IDpersonne`, `date`, `montant`, `listeIDdeplacement` | Porte un montant saisi et une seconde représentation, textuelle, des rattachements. |
| `personnes` | identité, nom, prénom | Sélecteurs et impression. |

Aucune clé étrangère, contrainte `CHECK` ou unicité métier n'est déclarée pour ces liens dans `DATA_Tables.py`.

## Requêtes et écritures observées

### Scénarios

- `DLG_Scenario_gestion.py`
  - recherche des dépendances par lecture complète de `scenarios_cat` puis décodage Python des reports `A...` ;
  - duplication par lecture de `scenarios`, insertion d'un nouvel en-tête, lecture puis insertion de toutes les lignes `scenarios_cat` ;
  - suppression directe dans `scenarios`, puis dans `scenarios_cat` pour le scénario supprimé.
- `DLG_Scenario.py`
  - lecture/écriture de `scenarios` et `scenarios_cat` ;
  - lecture de `cat_presences` ;
  - agrégation des `presences` de la personne/catégorie entre bornes inclusives ;
  - résolution d'un report automatique par lecture du scénario source, puis calcul récursif de sa catégorie ou de son total.
- `DLG_Scenario_saisie_report.py`
  - scénarios sources limités à la même personne ; le scénario en cours est exclu ;
  - catégories prévues lues dans `scenarios_cat`, catégories utilisées lues dans `presences`, référentiel lu dans `cat_presences`.

### Déplacements et remboursements

- `DLG_Saisie_deplacement.py`
  - dernier tarif et départ via le dernier `deplacements.IDdeplacement` ;
  - chargement d'un déplacement par `SELECT *` et indexation positionnelle ;
  - lecture de `remboursements.date` pour afficher le rattachement ;
  - lecture complète de `distances`, puis insertion ou mise à jour du trajet symétrique ;
  - insertion/mise à jour de `deplacements` avec `IDremboursement=0` dans tous les cas.
- `DLG_Saisie_remboursement.py`
  - lecture d'un remboursement, mais état des cases déterminé par `deplacements.IDremboursement` ;
  - nouveau remboursement : uniquement les déplacements non affectés ;
  - remboursement existant : déplacements non affectés ou déjà affectés à ce remboursement ;
  - écriture de `remboursements.listeIDdeplacement`, puis, dans une seconde connexion/transaction, mise à jour des `deplacements.IDremboursement`.
- `CTRL_Page_frais.py`
  - liste des déplacements et montant recalculé par `distance * tarif_km` ;
  - liste des remboursements et affichage des numéros depuis `listeIDdeplacement` ;
  - suppression d'un déplacement refusée s'il est rattaché ;
  - suppression d'un remboursement autorisée après confirmation, puis remise à zéro des déplacements associés.
- `DLG_Impression_frais.py`
  - sélection et impression depuis `deplacements` ; montant recalculé ; le rattachement affiché vient de `IDremboursement`.

## Règles métier confirmées par le code actuel

### Reports et dépendances entre scénarios

1. Un report manuel est stocké sous la forme `M+HH:MM` ou `M-HH:MM`.
2. Un report automatique est stocké sous la forme `A<IDscenario>;<IDcategorie>`.
3. La sélection d'un scénario source est limitée à la même personne et exclut la référence directe au scénario en cours.
4. La catégorie spéciale `1000` reporte le total du scénario source ; `999` représente « Sans catégorie ».
5. La valeur reportée est le **reste à réaliser** de la source : prévision, plus son propre report éventuel, moins son réalisé. Les chaînes de reports sont donc résolues récursivement.
6. Une source supprimée produit `+00:00` avec `ERREUR2`. Une source appartenant à une autre personne produit `+00:00` avec `ERREUR1`. L'écran colore ces erreurs et interdit la sauvegarde tant qu'elles sont affichées.

### Duplication et suppression d'un scénario

1. La duplication préfixe le nom par `Copie de ` et recopie les paramètres, prévisions, reports et périodes de réalisé.
2. Les références contenues dans les reports sont copiées **sans réécriture**. Elles continuent donc à viser les scénarios d'origine.
3. La suppression recherche les reports automatiques qui visent le scénario, affiche un premier avertissement, puis permet néanmoins de continuer.
4. Après confirmation finale, seules les lignes du scénario supprimé sont effacées. Les reports dépendants ne sont ni supprimés ni réécrits ; ils deviennent des références manquantes détectées ensuite comme `ERREUR2`.

### Déplacement, aller/retour, tarif et montant

1. `deplacements.distance` contient la distance utilisée pour le calcul du montant.
2. Cocher « aller/retour » multiplie la valeur courante par deux ; décocher la divise par deux.
3. Le montant affiché est toujours `distance stockée * tarif_km`. Aucun second multiplicateur lié au booléen aller/retour n'est appliqué.
4. Le champ `aller_retour` est stocké comme chaîne `"True"`/`"False"` et sert notamment au libellé de trajet.
5. Le cache `distances` est symétrique entre départ et arrivée et conserve un aller simple : la distance est divisée par deux avant sauvegarde quand la case aller/retour est cochée.
6. Distance ou tarif nuls restent validables après confirmation explicite.

### Lien Déplacement ↔ Remboursement

1. `deplacements.IDremboursement` pilote les cases cochées, les déplacements disponibles, l'interdiction de suppression d'un déplacement rattaché et l'impression.
2. `remboursements.listeIDdeplacement` est une chaîne d'identifiants séparés par `-` et pilote l'affichage « Déplacements rattachés » de la liste principale.
3. Un remboursement existant ne peut prendre que ses déplacements actuels et les déplacements non affectés ; ceux affectés à un autre remboursement ne sont pas proposés.
4. Le montant du remboursement est saisi indépendamment de la somme des déplacements. L'écart n'est qu'un avertissement visuel.
5. Un remboursement sans déplacement, ou de montant nul, reste validable après confirmation.
6. Un déplacement rattaché ne peut pas être supprimé.
7. Un remboursement rattaché peut être supprimé après avertissement ; tous les déplacements qui le pointent sont alors remis à `IDremboursement=0`.

## Comportements historiques accidentels ou douteux

| Priorité | Comportement caractérisé | Conséquence possible |
|---|---|---|
| Critique | `decimal.getcontext().prec = 2` est appliqué globalement dans l'écran Déplacement. | La précision porte sur deux chiffres significatifs, pas deux décimales. Exemple reproduit : `123 × 0,55` devient `68,00 €` au lieu de `67,65 €`. |
| Critique | Toute sauvegarde d'un déplacement, création **ou modification**, écrit `IDremboursement=0`. | Modifier un déplacement remboursé le détache silencieusement et laisse potentiellement `listeIDdeplacement` obsolète. |
| Critique | Aucun garde de cycle indirect dans la résolution récursive des reports. | Une boucle A→B→A peut finir en récursion non bornée plutôt qu'en erreur métier contrôlée. |
| Élevée | Deux sources de vérité pour les rattachements, lues par des écrans différents. | La liste des remboursements peut afficher des IDs différents des cases réellement cochées. |
| Élevée | Écriture du remboursement puis des déplacements dans deux connexions/transactions. | Une panne intermédiaire peut laisser le montant/la liste enregistrés sans les clés, ou l'inverse lors d'une reprise partielle. |
| Élevée | `OperationHeures` perd le signe pour un résultat négatif inférieur à une heure. | Exemple reproduit : `00:00 - 00:30` retourne `+0:30`. |
| Élevée | Supprimer un scénario référencé est autorisé et laisse des reports orphelins. | Les dépendants calculent zéro et bloquent leur prochaine sauvegarde, mais la base conserve l'incohérence. |
| Moyenne | Comparaison monétaire exacte de `float` avec zéro dans le message de rattachement. | Un écart résiduel binaire peut déclencher un avertissement trompeur. |
| Moyenne | Les codes postaux du cache `distances` sont convertis en `int`. | Les zéros initiaux sont perdus dans ce cache alors que les colonnes sont déclarées `VARCHAR(5)`. |
| Faible | Le gestionnaire de cases de l'ancien écran d'impression contient une mise à jour de la table `gadgets` avec un identifiant de déplacement. | Code vraisemblablement copié/collé ; effet parasite possible selon la variante wx utilisée. |

Ces constats décrivent le comportement actuel. Ils ne sont pas transformés en « nouvelles règles » pour Qt sans décision métier explicite.

## Dette technique distincte

- Absence de clés étrangères et de contraintes de domaine entre les tables du périmètre.
- Encodage des reports et listes d'identifiants dans des chaînes ad hoc.
- `listeIDdeplacement VARCHAR(300)` : capacité et intégrité non garanties par le modèle.
- `SELECT *` et lecture de colonnes par position dans l'écran Déplacement.
- SQL construit par interpolation `%` dans les écrans.
- Commits par ligne lors de certaines sauvegardes/duplications de scénarios ; opérations multi-tables non atomiques.
- Calcul du montant dupliqué dans plusieurs écrans et dans l'impression.
- Booléen aller/retour stocké en texte.
- Couplage fort UI, SQL, validation, confirmation et calcul métier dans les mêmes classes.
- Aucune commande de contrôle/réconciliation des reports orphelins ou des deux représentations de rattachement.

## Impossible à tester proprement sans extraction préalable

- Parcours complets des dialogues wxPython, focus, messages de confirmation et variantes Classic/Phoenix.
- Atomicité et reprise sur erreur des écritures réelles `GestionDB` avec injection d'une panne entre commits.
- Chaînes profondes et cycles de reports avec une vraie base et le cycle de rafraîchissement de la grille.
- Réconciliation sur une base utilisateur réelle entre `listeIDdeplacement` et `deplacements.IDremboursement`.
- Impression PDF et effets du gestionnaire de cases selon la plateforme.
- Concurrence éventuelle entre deux fenêtres modifiant le même remboursement/scénario.

Une extraction minimale des fonctions pures (décodage de report, arithmétique de durée, calcul monétaire, calcul de distance, plan de rattachement) et un adaptateur transactionnel seraient nécessaires avant des tests unitaires directs. Ce travail n'est volontairement pas inclus dans le présent lot.

## Tests ajoutés

- `tests/characterisation/source_legacy.py` : lecture AST, extraction ciblée de méthodes et lecture littérale de `DB_DATA`, sans import wxPython.
- `tests/characterisation/test_scenarios_wx.py` : 13 tests sur schéma, formats, sélection des sources, récursion, erreurs, duplication, suppression, sauvegarde et arithmétique historique.
- `tests/characterisation/test_frais_wx.py` : 14 tests sur schéma, aller/retour, montant, précision, cache, rattachement, double écriture, sélections, avertissements, suppressions et impression.

Commandes de validation du lot :

```bash
pytest -q tests/characterisation
python -m compileall -q tests/characterisation
```

Résultat obtenu lors de la préparation initiale : `27 passed` sur un miroir local minimal contenant les extraits exacts audités. Lors de l’intégration, les trois défauts confirmés (précision monétaire, détachement d’un déplacement remboursé et signe négatif des durées) sont exprimés comme résultats corrects attendus et marqués `xfail(strict=True)` jusqu’à leur correction, afin de ne pas figer les anomalies comme règles métier. Le connecteur GitHub de cette session ne fournissant pas de checkout exécutable, la commande doit être rejouée dans le dépôt complet après application du patch.

## Risques restant ouverts avant Qt

1. **Décider la source de vérité du rattachement.** Le candidat naturel est `deplacements.IDremboursement`; la chaîne historique doit être soit dérivée, soit contrôlée/réconciliée.
2. **Fixer la convention monétaire.** Précision, arrondi et type de stockage doivent être explicités avant de reproduire le calcul.
3. **Fixer la sémantique de `distance`.** Le code actuel stocke une distance totale dans `deplacements` mais un aller simple dans `distances`.
4. **Définir la politique sur les dépendances de scénario.** Refus de suppression, cascade, neutralisation ou conservation d'une erreur doivent devenir une décision explicite.
5. **Ajouter une détection de cycle** avant toute résolution de report automatique.
6. **Prévoir un diagnostic de données** avant migration Qt : reports mal formés/orphelins, cycles, références inter-personnes, remboursements divergents, déplacements pointant un remboursement absent.
