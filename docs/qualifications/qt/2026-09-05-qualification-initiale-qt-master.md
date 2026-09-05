# Qualification technique Qt — archive nettoyée

> **Statut de ce document**
>
> Archive de qualification technique du rail Qt.
>
> Les informations administratives GitHub de l'audit d'origine ont été retirées lorsqu'elles sont devenues obsolètes après la création de `wx/master` et `qt/master`, la fermeture des anciennes PR de qualification et la consolidation du projet.
>
> Ce document ne décrit donc **pas l'état GitHub courant**. Il conserve uniquement les éléments techniques utiles à la traçabilité de la qualification du HEAD qui a servi de point de départ à `qt/master`.

---

## 1. Référence technique qualifiée

Le HEAD Qt qualifié est :

`dad51c0f6aafeb77dd541b3873872fb2bebffa7c`

Ce commit réunissait :

- la convergence Qt issue de #381 ;
- le `master` wx courant au moment de la qualification (`860204ddbf297b4308dac7bef5e5f2b0e6e2bf2a`).

Ce HEAD a ensuite servi de point de départ au rail durable **`qt/master`**.

Le workflow de qualification associé était :

- **Validation et publication #1244**
- run `33960215727`
- conclusion : **success**
- Ubuntu 24.04 : **SUCCESS**
- Windows Server 2022 : **SUCCESS**
- Linux : **2123 passed, 5 skipped**

Le job Windows général de #1244 ne constituait pas à lui seul le smoke qwindows natif. La preuve qwindows spécialisée provenait de la qualification #381.

---

## 2. Garanties techniques conservées

| Garantie | État qualifié |
| --- | --- |
| Lifecycle worker dossier | ✅ |
| Lifecycle loader initial des personnes | ✅ |
| Rejet des payloads tardifs | ✅ |
| Pending annulé lors du close | ✅ |
| Clear Contrats avant lecture suivante | ✅ |
| Clear Généralités | ✅ |
| Clear Questionnaire | ✅ |
| Clear Scénarios | ✅ |
| Clear Frais | ✅ |
| Séquence A→B | ✅ |
| Séquence A→B→C | ✅ |
| Rejet du stale A | ✅ |
| Fermeture avec worker réellement bloqué | ✅ |
| 8 onglets | ✅ |
| Plugin Windows natif | ✅ |
| Vraie `QEventLoop` | ✅ |
| Mesure correcte du premier affichage | ✅ |
| Démarrage ≤ 3 s | ✅ |
| RSS ≤ 220 Mo | ✅ |
| Dépendances directes ≤ 4 | ✅ |
| Aucun `QThread.terminate()` dans le lifecycle | ✅ |
| Aucune écriture DB depuis le rail Qt qualifié | ✅ |
| Pas de dépendance wxPython directe dans l'UI Qt | ✅ |
| Mapping Contrats historique | ✅ |
| Questionnaire historique | ✅ |
| Scénarios/Frais historiques | ✅ |
| Qualifications historiques | ✅ |
| Présences : reader + projection + tests historiques | ✅ |

### Présences

La donnée Présences était qualifiée côté reader/projection, mais n'était pas encore raccordée au worker individuel Qt. Cette distinction reste volontaire :

**donnée qualifiée ≠ écran raccordé**.

---

## 3. Lifecycle QThread

Le lifecycle qualifié reposait notamment sur :

- `CLOSE_WAIT_TIMEOUT_MS = 100` ;
- un état explicite de fermeture ;
- le suivi séparé du worker dossier et du loader de personnes ;
- le refus de démarrer ou rattacher un nouveau worker pendant la fermeture ;
- l'annulation du pending et de la sélection ;
- `quit()` sur les threads suivis ;
- un `wait()` court dont l'échec est traité ;
- conservation de l'ownership tant que le thread vit ;
- `event.ignore()` lorsque nécessaire ;
- nettoyage sur `finished` et `deleteLater()` ;
- remise à `None` des références ;
- nouvelle tentative de fermeture après nettoyage ;
- attente finale sans destruction forcée du QThread.

Le loader initial des personnes suivait la même discipline : son résultat était abandonné lorsque la fermeture avait déjà été demandée.

### Limite connue

Une lecture DB synchrone réellement bloquée n'est pas annulable par magie. Si le driver ne rend jamais la main, l'attente finale peut durer indéfiniment.

Cette limite concerne **l'annulation de l'I/O DB**, pas la sécurité du lifecycle QThread.

---

## 4. Runtime Qt / qwindows

Le smoke qualifié utilisait une vraie **`QEventLoop`**.

Le scénario de worker bloquant utilisait `threading.Event`, sans boucle artificielle basée principalement sur `QApplication.processEvents()+sleep`.

Le benchmark Windows :

- créait un environnement Python 3.11 ;
- installait les dépendances Qt ;
- activait l'exigence Windows native ;
- supprimait un éventuel `QT_QPA_PLATFORM` forcé ;
- exécutait le smoke runtime ;
- exécutait ensuite le benchmark.

La qualification native #381 avait validé :

- Windows Server 2022 ;
- Python 3.11.9 ;
- PySide6 6.11.2 ;
- plugin `windows` ;
- **21 tests ciblés PASS** ;
- benchmark PASS ;
- smoke PASS ;
- aucun QThread actif détruit ;
- aucun payload tardif appliqué ;
- 8 onglets ;
- A→B ;
- A→B→C ;
- clear immédiat ;
- fermeture différée sûre.

---

## 5. Frugalité

Budgets qualifiés :

- démarrage : **3,0 s maximum** ;
- RSS : **220 Mo maximum** ;
- dépendances directes : **4 maximum**.

Dépendances UI observées lors de la qualification :

- `PySide6`
- `qt-material`

Soit **2 dépendances directes**.

Mesures du benchmark natif Windows #381 :

- démarrage benchmark : **0,59 s** ;
- RSS : **67 Mo** ;
- dépendances directes : **2**.

Le premier affichage était mesuré immédiatement après `window.show()`, puis transmis explicitement au `FrugalityProbe`, afin que les traitements asynchrones ultérieurs ne polluent pas la mesure du premier rendu.

---

## 6. Protections métier historiques

### Contrats

- `2999-01-01` → `Indétermin.` dans le contexte Contrats ;
- une date de rupture prend priorité sur la date de fin ;
- suffixe `-R` conservé ;
- couverture d'un cas historique réel de rupture.

### Questionnaire

- une réponse sauvegardée vide reste une réponse vide ;
- elle ne réactive pas une valeur par défaut ;
- `##DOCUMENTS##` n'est pas affiché comme réponse métier.

### Scénarios / Frais

Les caractérisations historiques utilisaient `Exemple_TDATA.dat` et verrouillaient notamment les données et formats historiques nécessaires à la migration.

### Qualifications

Le sentinel `2999-01-01` ne reçoit pas automatiquement la sémantique Contrats `Indétermin.`.

### Présences

La base exemple qualifiait notamment :

- **1 026 présences pour la personne 3** ;
- date affichée uniquement sur la première ligne d'un même jour ;
- horaires ;
- durée ;
- catégorie/intitulé ;
- périodes de vacances.

---

## 7. Risques et preuves restantes

### Bloqueur automatisable au moment de la qualification

**Aucun démontré.**

### Risque connu

Absence d'annulation forcée fiable d'une requête DB synchrone bloquée.

### Amélioration CI souhaitable

Le qwindows natif spécialisé devrait idéalement devenir un gate permanent du workflow Qt, afin que la preuve soit rejouée directement à chaque évolution de `qt/master`.

### Validation interactive

La qualification automatisée ne remplace pas un smoke interactif réel sur un poste Windows utilisateur.

Il faut distinguer :

- CI Windows GitHub : qualifiée ;
- qwindows natif automatisé : qualifié ;
- tests sur base historique versionnée : qualifiés ;
- validation interactive utilisateur : distincte.

---

# Verdict technique archivé

## GO TECHNIQUE AUTOMATISÉ DU HEAD Qt QUALIFIÉ

Le HEAD :

`dad51c0f6aafeb77dd541b3873872fb2bebffa7c`

avait satisfait les garanties ayant conduit aux validations lifecycle et qwindows.

Ce HEAD est désormais conservé dans l'histoire du projet comme point de départ du rail durable **`qt/master`**.

---

## Éléments volontairement retirés de l'audit d'origine

Ont été supprimés de cette archive :

- les affirmations indiquant #366 comme PR encore ouverte ;
- les recommandations de fermeture de #377, #378 et #380 ;
- les tableaux d'état administratif de ces PR ;
- la formule « merge master non autorisé — attente validation Franck » devenue sans objet avec l'architecture à deux rails ;
- les répétitions détaillant plusieurs fois la même convergence ;
- les informations de statut GitHub devenues périssables.

La référence GitHub courante doit être lue directement dans le dépôt et dans la documentation d'architecture des rails `wx/master` / `qt/master`.
