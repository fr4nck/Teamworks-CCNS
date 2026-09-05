# Archive — contexte fonctionnel et migration Qt récupéré des conversations

Date de capture : 2026-09-05

> Cette archive conserve des observations et conventions techniques issues des travaux de migration. Les tests et le code courant restent la preuve prioritaire. Une donnée historique décrite ici ne doit pas être transformée en règle métier sans vérification.

## 1. Principe général de migration

- wxPython reste la référence de production pendant la transition.
- Qt est le rail cible pour la modernisation UI.
- Les readers, projections et règles métier doivent être isolés du toolkit UI lorsque possible.
- Un écran wx historique n'est pas automatiquement une spécification : caractériser avant de reproduire.
- Les données historiques utilisées pour caractériser les comportements proviennent notamment de `teamworks/Static/Exemples/Exemple_TDATA.dat`.

## 2. Présences

Travail historique qualifié côté lecture/projection Qt :

- records de domaine ;
- lecture historique sans wx ;
- tests sur base historique ;
- protocole de projection de vue ;
- conventions de projection ;
- adapter de lecture composable.

Commits historiques repérés lors des conversations :

- `1dfc527` — domain records ;
- `06ad09c` — lectures historiques sans wx ;
- `09f559c` — tests base historique ;
- `287428c` — protocole de projection ;
- `bbb71be` — conventions historiques ;
- `2a63843` — tests ;
- `3b79843` — read adapter composable ;
- `ff8a8e1` — test adapter.

### Projection historique caractérisée

Colonnes :

- Date ;
- Vacances ;
- Horaires ;
- Durée ;
- Intitulé.

Conventions observées :

- date française complète ;
- date répétée laissée vide sur les lignes suivantes du même jour ;
- heure `08:00` projetée en `8h00` ;
- certaines durées historiques reposent sur `timedelta.seconds`, ce qui peut faire boucler une durée négative modulo 24 h : ne pas reproduire sans arbitrage ;
- en cas de chevauchement de périodes de vacances, la dernière période correspondante était retenue dans le comportement caractérisé.

Données historiques relevées :

- personne 3 : **1 026 lignes de présence** ;
- total relevé : **5 841** ;
- catégories : **13** ;
- périodes de vacances : **22**.

Point important : le reader/projection Présences était qualifié, mais l'écran Qt restait à raccorder. **Donnée qualifiée ≠ écran raccordé.**

Présences reste un candidat logique pour un prochain raccordement fonctionnel Qt.

## 3. Qualifications

Comportement historique caractérisé notamment sur la personne 3 :

- BAFA ;
- AFPS.

Exemples historiques :

- BAFA : `2006-01-20` → `2999-01-01` ;
- médical : `2009-01-01` → `2009-04-01` ;
- casier : `2009-05-15` → `2010-05-15`.

Convention importante : dans le domaine Qualifications, le sentinel `2999-01-01` était formaté comme une date (`01/01/2999`) et **ne devait pas recevoir automatiquement la sémantique Contrats `Indétermin.`**.

Commit de caractérisation repéré : `4b2321ed`.

L'écran Qt Qualifications était encore essentiellement un shell lors des travaux historiques.

## 4. Recrutement

L'écran historique réellement identifié est :

`CTRL_Page_candidatures.py`

et non un agrégat supposé `CTRL_Recrutement.py`.

Colonnes candidatures observées :

- Dépôt ;
- Offre d'emploi ;
- Disponibilités ;
- Fonction(s) ;
- Affectation(s) ;
- Décision ;
- Réponse.

Entretiens :

- Date ;
- Heure ;
- Avis ;
- Commentaire.

Aucun chargement métier Qt complet n'avait été démontré au moment de la capture. Ne pas déclarer une régression simplement parce qu'un shell Qt ne reproduit pas encore un écran non migré.

## 5. Contrats

Conventions historiques protégées :

- `2999-01-01` → `Indétermin.` **dans le contexte Contrats uniquement** ;
- une date de rupture remplace la date de fin affichée ;
- suffixe `-R` ajouté lorsque la rupture est utilisée.

Constantes historiques repérées :

- `EMPTY = "—"` ;
- `INDEFINITE_CONTRACT_END = "2999-01-01"` ;
- `INDEFINITE_CONTRACT_LABEL = "Indétermin."`.

Commits historiques associés :

- `0c9067d` ;
- `8e798ec` ;
- `2ae0052` ;
- `550de97` ;
- `336b371` ;
- `c7f44bbc` ;
- `31e71c28`.

Un cas historique testé utilisait notamment `27/12/2011-R`.

## 6. Questionnaire

Données historiques relevées :

- 6 questions ;
- 2 catégories ;
- 6 choix ;
- 49 réponses.

Exemples personne 3 :

- `XD16252` ;
- `2008-12-03` ;
- `Permanent` ;
- aucune réponse document ;
- `Moto, Vélo` ;
- `41`.

Règles caractérisées :

- une réponse sauvegardée, même vide, prévaut sur le défaut ;
- une réponse vide sauvegardée doit donc rester vide/`—`, sans réapparition automatique de la valeur par défaut ;
- `##DOCUMENTS##` est un sentinel technique et ne doit jamais être affiché comme réponse métier.

Commits historiques repérés :

- correction : `96c7eef` ;
- tests : `4cd14f5` ;
- base historique : `aebe502`.

Ne pas modifier ce mapping sans anomalie démontrée.

## 7. Scénarios et Frais

La caractérisation historique s'appuie sur la base exemple et contient notamment :

- scénario `Année 2009` ;
- période historique ;
- description vide ;
- ordre historique des déplacements ;
- libellé `QUIMPER <--> BREST` ;
- montant `30.00 €` ;
- référence `N°1` ;
- `QUIMPER -> LANDERNEAU` ;
- montant `16.60 €`.

Les tests de caractérisation doivent continuer à distinguer comportement observé et règle souhaitable. Exemple : une durée négative mal projetée dans `OperationHeures` est un défaut à corriger, pas une convention à reproduire.

## 8. Qt — fichiers historiquement sensibles

Fichiers particulièrement liés à la convergence runtime/lifecycle Qt :

- `poc/qt-theme/benchmark_models.py` ;
- `poc/qt-theme/benchmark_windows.cmd` ;
- `poc/qt-theme/frugality.py` ;
- `poc/qt-theme/launcher.py` ;
- `poc/qt-theme/pilot_generalities.py` ;
- `poc/qt-theme/runtime_async_smoke.py` ;
- `tests/test_qt_blocking_thread_lifecycle_runtime.py` ;
- `tests/test_qt_individual_async_contract.py`.

Frontières données / Présences repérées :

- `domain/repositories/individual_activity_data.py` ;
- `infrastructure/persistence/individual_activity_reader.py` ;
- `poc/qt-theme/data_adapter.py` ;
- `poc/qt-theme/presence_projection.py` ;
- `poc/qt-theme/presence_read_adapter.py`.

Les chemins peuvent évoluer avec la migration ; cette liste indique les zones historiquement qualifiées, pas une architecture figée.

## 9. Lifecycle Qt — invariants à protéger

Les travaux de qualification avaient verrouillé :

- clear immédiat de l'état d'un salarié avant application des données du suivant ;
- rejet des payloads tardifs ;
- garde contre une sélection devenue obsolète ;
- annulation du pending lors de la fermeture ;
- conservation de l'ownership des QThread tant qu'ils sont actifs ;
- aucune destruction forcée via `QThread.terminate()` ;
- vraie `QEventLoop` pour le smoke runtime ;
- fermeture différée sûre en présence d'un worker bloqué ;
- mesure du premier `show()` sans pollution par les traitements asynchrones ultérieurs.

Limite connue : une I/O DB synchrone qui ne rend jamais la main n'est pas forcément annulable. La bonne réponse est un lifecycle sûr, pas une destruction forcée du thread.

## 10. Frugalité Qt qualifiée

Budgets historiques :

- démarrage ≤ 3 s ;
- RSS ≤ 220 Mo ;
- dépendances directes ≤ 4.

Qualification native relevée :

- démarrage benchmark : ~0,59 s ;
- RSS : ~67 Mo ;
- 2 dépendances UI directes (`PySide6`, `qt-material`).

Ces chiffres sont des mesures d'une qualification datée ; les futures versions doivent les remesurer.

## 11. Documents RH

Besoins récupérés des conversations :

- modèles Microsoft Office ;
- attestations d'emploi ;
- autorisations de travail des mineurs ;
- attestations d'expérience ;
- documents liés au contrat et au parcours salarié ;
- éventuels besoins France Travail selon la démarche concernée.

Règle de rendu : une donnée absente ne doit pas laisser un marqueur technique brut de type `<mot_cle>`. Lorsqu'une complétion humaine est nécessaire, laisser un emplacement propre et remplissable.

Les données employeur doivent provenir d'une source structurée et ne pas être dupliquées manuellement dans chaque modèle.

Les PR #312/#313 couvrent une partie des fondations/catalogue ; #383 conserve le travail restant du sélecteur/publipostage à réévaluer.

## 12. Portail / accueil / continuité associative

Besoins récupérés et sauvegardés également dans `docs/decisions/2026-09-05-recuperation-decisions-conversations.md` :

- RSS / actualités ;
- échéances de conformité, notamment documents salariés et DUERP ;
- ETP sur période hors CEE ;
- annuaire institutionnel et professionnel ;
- bureau / CA ;
- collectivités partenaires ;
- interlocuteur CTG ;
- mémento protégé ;
- synchronisation téléphone adaptée ;
- possibilité pour Cindy d'ajouter un salarié via le Portail.

Contacts institutionnels cités : SDJES35, PST35, France Travail, URSSAF, DREETS/DIRECCTE, assurance, prévoyance, COSMOS ou autre syndicat du sport, CAF, collectivités, CTG.

Tous les contacts ne doivent pas être distribués à tous les rôles. Le coordinateur sportif ne doit pas recevoir automatiquement l'intégralité de l'annuaire professionnel. L'équipe utilise Signal. CardDAV n'est pas destiné à être imposé aux téléphones personnels non professionnels.

Finalité : préserver la connaissance institutionnelle de l'association pour qu'elle survive au départ éventuel d'une personne clé.

## 13. Connecthys et 02switch

- Connecthys doit être remplacé par le futur Portail avec des fonctions qui dépassent son périmètre actuel.
- L'audit code n'avait pas démontré de dépendance bloquante Connecthys, mais une qualification terrain restait nécessaire.
- 02switch héberge les mails et WordPress.
- Un éventuel rapatriement futur de 02switch reste une **question ouverte**, pas une décision.

## 14. Contexte release historique

Ancien merge de contexte :

- PR #368 ;
- merge commit `440e0e9d98abb48262c5a910c3c99d7dd0d7b8e1` ;
- titre historique : `Merge pull request #368 from fr4nck/ccns/session-actual-hr-current`.

Règle à retenir : ne jamais déduire la capacité à livrer une RC/installable Qt du seul GO de qualification du POC. Les jobs packaging peuvent être distincts ou skipped.

## 15. Convention d'identité PMSL35

PMSL35 désigne un homologue/agent disposant de son propre compte GitHub permettant d'identifier ses modifications. **PMSL35 n'est pas un serveur.**

Cette note est conservée uniquement pour éviter de réintroduire une interprétation technique erronée dans la documentation ou les audits futurs.
