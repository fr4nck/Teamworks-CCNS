# Teamworks Vanilla — suivi des bugs et correctifs

## Objectif

Ce fichier recense les anomalies réellement présentes dans la version originale de Teamworks (`Noethys/Teamworks`) que nous avons rencontrées ou mises en évidence pendant le développement de Teamworks-CCNS.

Objectifs :

1. disposer d'un **Teamworks Vanilla corrigé et utilisable** pendant que Teamworks-CCNS continue son développement ;
2. séparer strictement les bugs historiques des régressions de migration, de la modernisation UI et des extensions CCNS ;
3. préparer des correctifs minimaux éventuellement transmissibles au projet d'origine.

## Référence amont

- Projet original : `Noethys/Teamworks`
- Base commune : `00bd52ef85853eb617361a15c2f0cc0cfa1b898e`
- Fork de développement : `fr4nck/Teamworks-CCNS`

## Résultat du premier tri

L'audit des **8 familles candidates initiales est terminé**.

| Famille initiale | Classement | Conclusion |
|---|---|---|
| Parentage `StaticBox` / contrôles | **Python 3 / Phoenix** | Le code historique existe bien dans Vanilla, mais les corrections rencontrées sont liées au comportement plus strict de wxPython Phoenix. Ne pas backporter dans Vanilla sans preuve d'un défaut sous son environnement d'origine. |
| Sizers / layouts | **Mixte** | Les warnings de flags (`ALIGN_*` + `EXPAND`) sont plutôt Phoenix. En revanche, les grilles des dialogues de sauvegarde déclarées avec 2 lignes alors que 3 éléments sont ajoutés sont bien présentes dans Vanilla : bug Vanilla confirmé. |
| Parsing des dates personne | **Régression de notre fork** | Vanilla contient bien `datetime.date(annee, mois, jour)`. La valeur erronée `datetime.date(annee, mois, annee)` a été introduite par notre commit `4914e6f` puis restaurée par `416d98b`. À exclure du backlog Vanilla. |
| Sauvegardes / sources absentes | **Vanilla** | `os.listdir(rep)` est appelé sans vérifier l'existence du répertoire dans le code original. Bug confirmé. |
| Gadgets / absence de sélection | **Vanilla** | Le code original lit `GetItemData(-1)` avant de vérifier qu'un élément est sélectionné et ne protège pas toutes les bornes haut/bas. Bug confirmé. |
| Aperçu e-mail / navigation | **Vanilla** | La condition d'avance est décalée d'une unité et les listes vides / indices hors bornes ne sont pas protégés. Bug confirmé. |
| Listes / contrôleurs recrutement | **UI/UX moderne** | Les correctifs candidats utilisent déjà `section.GetContentPanel()`, les tokens UI et un découplage owner/parent issu de notre refonte. Ils corrigent notre architecture moderne, pas Vanilla. |
| Icônes / ressources absentes | **Vanilla — robustesse** | Le contrôle original ouvre directement le fichier avec `Image.open()` et suppose un chemin valide. Une ressource absente peut donc casser la création d'un bouton. Le principe du correctif est Vanilla, mais le patch actuel doit être réécrit minimalement pour rester compatible avec le socle historique. |

## Backlog Vanilla confirmé

### VFIX-001 — Répertoires de sauvegarde absents

**Zone :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

**Défaut Vanilla :** les sources sont parcourues avec `os.listdir(rep)` sans contrôle préalable. Si un répertoire attendu n'existe pas, l'ouverture de l'écran ou une sauvegarde automatique peut échouer.

**Correctif trouvé dans Teamworks-CCNS :** `270935523811459fcf26bf5242af697a363b0270`.

**Backport Vanilla attendu :** test `os.path.isdir(rep)` puis liste vide / `continue`.

**État :** diagnostic terminé ; correctif minimal connu ; backport et test Vanilla à faire.

---

### VFIX-002 — Mauvais nombre de lignes dans les grilles de sauvegarde

**Zone :** `teamworks/Dlg/DLG_Config_sauvegarde.py`

**Défaut Vanilla :** plusieurs `wx.FlexGridSizer(rows=2, cols=1, ...)` reçoivent en réalité trois éléments (introduction, contenu, boutons). Cette incohérence est présente dans le source original.

**Correctif trouvé dans Teamworks-CCNS :** `d2c654493eabd3887cee2bd1651c540db2def400` passe ces grilles à 3 lignes.

**État :** diagnostic terminé ; correctif minimal connu ; backport et test Vanilla à faire.

---

### VFIX-003 — Gadgets : actions sans sélection et bornes haut/bas

**Zone :** `teamworks/Dlg/DLG_Config_gadgets.py`

**Défaut Vanilla :** `Options()` appelle `GetItemData(index)` avant le test `index == -1`. Les actions de déplacement ne protègent pas systématiquement le premier/dernier élément et la sélection peut être hors limites.

**Correctif trouvé dans Teamworks-CCNS :** `6bd223c9ce2dcd915934071c9b452b7bb907025f`.

**État :** diagnostic terminé ; correctif minimal connu ; backport et test Vanilla à faire.

---

### VFIX-004 — Aperçu e-mail : navigation hors limites

**Zone :** `teamworks/Dlg/DLG_Apercu_fusion_emails.py`

**Défaut Vanilla :** `OnBoutonAvancer()` autorise encore l'avance lorsque l'index pointe déjà sur le dernier élément (`index < len(self.donnees)`), puis `Navigation()` sélectionne sans vérifier la nouvelle borne. Les boutons premier/dernier ne protègent pas non plus une liste vide.

**Correctif trouvé dans Teamworks-CCNS :** `79cdb0e02a4e5d34a8c0ebf8e4a6ad7381ff695d`.

**État :** diagnostic terminé ; correctif minimal connu ; backport et test Vanilla à faire.

---

### VFIX-005 — Boutons image : ressource absente non tolérée

**Zone :** `teamworks/Ctrl/CTRL_Bouton_image.py`

**Défaut Vanilla :** le contrôle historique suppose que `cheminImage` est valide puis appelle directement `Image.open(self.cheminImage)`. Une ressource manquante ou illisible peut donc empêcher la création du bouton.

**Correctif de référence côté Teamworks-CCNS :** `10e80e0a2e7a677cbb078c5b42234a2cc0806137`, verrouillé par `0225b2ba10c12f1c1208d136336636ed7d12ec9c`.

**Attention :** le correctif actuel dépend de notre contrôle de bouton modernisé et de `pathlib`. Le backport Vanilla devra uniquement ajouter une tolérance minimale compatible avec son Python historique, sans importer le design system ni le code moderne.

**État :** diagnostic terminé ; stratégie de correction connue ; patch Vanilla à reconstruire et tester.

## Éléments sortis du backlog Vanilla

### PY3/Phoenix

Les correctifs de parentage `StaticBox` (`8f60b70`, `c10dddd`, `e2bf297`, `9a15534`, `3ddb6a8`, `6885527`, `c240179`, `dab7fef`) restent suivis dans le chantier Python 3/Phoenix. Le source original utilise effectivement ces parentages historiques, mais l'anomalie rencontrée chez nous correspond au durcissement de wxPython Phoenix et n'est pas retenue comme bug Vanilla exploitable à ce stade.

Les corrections de flags de sizers du type `ALIGN_RIGHT | EXPAND` relèvent du même classement lorsqu'elles ne correspondent pas à une erreur structurelle indépendante de Phoenix.

### Régression de notre fork

Le parsing de date corrigé par `416d98b` n'est pas un bug Vanilla : le source original contenait déjà la bonne expression `datetime.date(annee, mois, jour)`. L'erreur avait été introduite accidentellement lors du commit `4914e6f`.

### UI/UX moderne

Les correctifs de contrôleurs/listes recrutement (`483199f`, `eaab713`, `ac24ae1`, `b4c6508`, `a3ae40b`) interviennent sur des composants déjà transformés par notre refonte (`section.GetContentPanel()`, tokens sémantiques, séparation owner/parent). Ils restent dans le chantier UI/UX et ne doivent pas être injectés dans Vanilla.

## Mesure d'avancement

### Audit initial

- familles candidates : **8** ;
- familles triées : **8 / 8** ;
- **audit initial : 100 %**.

### Lot Vanilla actuellement confirmé

Nous avons **5 correctifs Vanilla confirmés** à préparer.

Pour mesurer l'avancement du lot, chaque correctif vaut 4 étapes :

1. bug confirmé dans Vanilla ;
2. correction minimale identifiée ;
3. correction backportée sur un socle Vanilla ;
4. correction testée sur ce socle.

État actuel :

| Correctif | Confirmé | Correction connue | Backporté | Testé | Avancement |
|---|---:|---:|---:|---:|---:|
| VFIX-001 Sauvegarde / dossier absent | Oui | Oui | Non | Non | 50 % |
| VFIX-002 Grilles sauvegarde | Oui | Oui | Non | Non | 50 % |
| VFIX-003 Gadgets | Oui | Oui | Non | Non | 50 % |
| VFIX-004 Aperçu e-mail | Oui | Oui | Non | Non | 50 % |
| VFIX-005 Icônes absentes | Oui | Oui (à réécrire) | Non | Non | 50 % |

**Progression du lot Vanilla connu : 50 %.**

Ce 50 % signifie que le diagnostic et la solution sont connus. Il ne signifie pas encore qu'une version Vanilla corrigée est prête à être utilisée : le backport et les tests sur le socle historique restent à réaliser.

## Principe du futur Teamworks Vanilla corrigé

**Teamworks original + corrections de bugs uniquement.**

Pas de migration Python 3, pas de nouveau thème, pas de CCNS et pas de fonctionnalités supplémentaires.

La prochaine étape est donc de créer une branche ou un fork strictement issu du socle Vanilla, d'y appliquer `VFIX-001` à `VFIX-005` sous forme de patches minimaux, puis de les tester avant de considérer la première version utilisable.
