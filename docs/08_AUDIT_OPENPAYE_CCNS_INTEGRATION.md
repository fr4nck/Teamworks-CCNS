# Audit OpenPaye / CCNS Sport — répartition des responsabilités et intégration Teamworks

**Statut : étude technique vivante**  
**Date : 27 août 2026**

> Ce document complète `docs/07_ETUDE_PAIE_FRANCE.md`. Il ne constitue pas une feuille de route concurrente de `ROADMAP.md` et n'attribue aucun identifiant `TW-*`.

## 1. Conclusion

OpenPaye est un candidat crédible comme **moteur de paie spécialisé** pour une structure relevant de la convention collective nationale du Sport (IDCC 2511).

Teamworks-CCNS doit rester le **logiciel RH et de contrôle employeur en amont de la paie**. Il ne doit pas reproduire le calcul complet d'un bulletin, les cotisations, le prélèvement à la source ou la DSN.

Principe cible :

```text
Teamworks-CCNS
  salarié / contrat / classification / temps de travail
  contrôles CCNS / CDD / CEE / ancienneté / absences
                    |
                    | données RH et variables de paie validées
                    v
                OpenPaye
  calcul du bulletin / cotisations / PAS / DSN / éditions
```

La présence d'une même règle dans les deux logiciels n'est pas nécessairement une duplication à supprimer :
- **Teamworks** vérifie la conformité avant la signature du contrat ou avant transmission en paie ;
- **OpenPaye** applique la règle dans le calcul de paie effectif.

## 2. Ce qu'OpenPaye confirme pour la convention Sport

La documentation publique OpenPaye liste explicitement :

- **Sport — IDCC 2511**.

OpenPaye indique maintenir, pour les conventions collectives prises en charge :
- les classifications conventionnelles ;
- les salaires minimums conventionnels ;
- les rémunérations des apprentis, alternants et stagiaires ;
- les retraites complémentaires ;
- les taux de prévoyance obligatoires ;
- les majorations de nuit, jours fériés et dimanche ;
- les primes d'ancienneté ;
- les différentes primes conventionnelles ;
- les maintiens de salaire en cas d'arrêt de travail.

Source : https://openpaye.co/docs/liste-des-conventions-collectives-sur-openpaye

Une mise à jour publiée en octobre 2024 montre également une maintenance spécifique de la branche Sport : le CQP de technicien des secteurs acrobatiques, rythmiques et d'expression y est positionné au minimum en groupe 3.

Source : https://openpaye.co/docs/newsletter-du-11-octobre-2024

## 3. Ce que Teamworks-CCNS contrôle déjà

L'audit du code `master` confirme que Teamworks-CCNS possède déjà des contrôles spécialisés qui ont une valeur propre en amont de la paie.

### 3.1 Classification et minima 2026

La grille intégrée correspond aux groupes G1 à G8 :

| Groupe | Minimum 2026 |
|---|---:|
| G1 | 1 848,42 € / mois |
| G2 | 1 885,14 € / mois |
| G3 | 1 997,87 € / mois |
| G4 | 2 099,37 € / mois |
| G5 | 2 333,99 € / mois |
| G6 | 2 865,97 € / mois |
| G7 | 40 597,94 € / an |
| G8 | 46 833,81 € / an |

Le moteur distingue correctement les minima mensuels G1-G6 des minima annuels G7-G8 et compare également le minimum conventionnel au SMIC applicable.

Fichiers :
- `domain/convention/ccns_salary_grid_data.py`
- `application/control/ccns_contract_compliance.py`
- `application/control/contract_compensation_preflight.py`

### 3.2 Temps partiel

Teamworks intègre notamment :
- la majoration du minimum de **5 % jusqu'à 10 h hebdomadaires** ;
- la majoration de **2 % au-delà de 10 h et en dessous de 24 h** ;
- les durées minimales CCNS selon le nombre de jours travaillés ;
- le traitement des dérogations ;
- les heures complémentaires et leur plafond ;
- les compléments d'heures par avenant et leurs plafonds.

Fichiers :
- `domain/convention/part_time_minimum_increase.py`
- `domain/convention/part_time_working_time.py`

### 3.3 Classification réelle du poste

Teamworks ne se contente pas de mémoriser un groupe. Le domaine sait contrôler :
- une évolution de poste impliquant une reclassification ;
- la polyvalence permanente avec seuil supérieur à 20 % sur une activité relevant d'un groupe supérieur ;
- l'exercice temporaire d'une fonction supérieure pouvant entraîner une prime.

Fichier : `domain/convention/classification_rules.py`

Cette logique doit rester dans Teamworks : OpenPaye doit recevoir le **résultat de la décision de classification**, pas décider à la place de l'employeur de la réalité du poste occupé.

### 3.4 Ancienneté

Teamworks sait calculer et alerter sur la prime d'ancienneté CCNS :
- groupes G1 à G6 ;
- progression de 1 % du SMC G3 par période de 24 mois de travail effectif ;
- règle particulière G1 après 3 ans d'ancienneté dans l'entreprise ;
- plafond de 15 % ;
- proratisation selon le temps de travail.

Fichier : `domain/convention/seniority.py`.

OpenPaye annonce également gérer les primes d'ancienneté conventionnelles. La répartition retenue est donc :
- Teamworks : **calcul attendu / alerte / contrôle** ;
- OpenPaye : **montant final calculé et porté au bulletin**.

À terme, un rapprochement entre le montant attendu par Teamworks et le bulletin OpenPaye serait un contrôle de second niveau utile.

### 3.5 CEE

OpenPaye sait établir un bulletin pour un **contrat d'engagement éducatif (CEE)** et propose le type de contrat `60-Contrat d'engagement éducatif`, avec gestion du nombre de jours, du taux journalier et de la base forfaitaire.

Source : https://openpaye.co/docs/contrat-dengagement-%C3%A9ducatif-cee

En revanche, la documentation publique inspectée ne démontre pas qu'OpenPaye contrôle en amont :
- le plafond de 80 jours sur 12 mois consécutifs ;
- la moyenne de 48 h sur l'ensemble des contrats ;
- les limites propres aux travailleurs mineurs.

Teamworks possède précisément ces garde-fous dans `domain/contracts/cee_contract_guardrails.py`.

**Décision : conserver ces contrôles dans Teamworks.** OpenPaye reçoit ensuite les éléments nécessaires au calcul du bulletin CEE.

## 4. Répartition cible des responsabilités

| Domaine | Teamworks-CCNS | OpenPaye |
|---|---|---|
| Dossier RH salarié | **Maître** | Copie utile à la paie |
| Contrat et avenants | **Maître RH / juridique** | Copie nécessaire au calcul |
| Choix du groupe CCNS | **Maître de la décision RH** | Applique la classification reçue |
| Minima CCNS / SMIC | Contrôle préalable | **Calcul final de paie** |
| Ancienneté | Historique + contrôle attendu | **Calcul de la ligne de paie** |
| Temps partiel / dérogations | **Contrôle juridique** | Valorisation sur bulletin |
| Heures complémentaires | Contrôle des limites | **Valorisation paie** |
| Nuit / dimanche / fériés | Contrôle possible des données reçues | **Majorations de paie** |
| CDD / motifs / échéances | **Maître RH** | Données nécessaires à la paie / DSN |
| CEE : plafonds et mineurs | **Maître du contrôle RH** | Calcul du bulletin CEE |
| Absences | Demande, validation, historique RH | **Impact financier et maintien de salaire** |
| Cotisations | Hors périmètre | **Maître** |
| Prélèvement à la source | Hors périmètre | **Maître** |
| DSN | Hors périmètre | **Maître** |
| Bulletin de paie | Hors périmètre | **Maître** |

## 5. Données qu'OpenPaye peut recevoir

La documentation d'intégration OpenPaye montre qu'un contrat peut être créé ou mis à jour avec notamment :
- matricule salarié ;
- établissement ;
- statut professionnel ;
- date de début ;
- date d'ancienneté ;
- date prévisionnelle de fin ;
- type de contrat ;
- motif de recours au CDD ;
- convention collective ;
- emploi conventionnel ;
- nature d'emploi ;
- régime de retraite ;
- cas particuliers ;
- forfait jours ;
- type de salaire ;
- salaire mensuel ;
- salaire horaire ;
- horaires du lundi au dimanche ;
- nombre d'heures mensuelles ;
- heures mensuelles majorées ;
- indicateur temps partiel ;
- nombre de jours travaillés ;
- nombre annuel de jours au contrat.

Source : https://openpaye.co/docs/connecte-openpaye-a-dautres-applications

OpenPaye expose une API dont l'adresse de base est :

`https://api.openpaye.co/`

La documentation annonce les méthodes `GET`, `PUT` et `POST` avec authentification **Basic Auth** par identifiant et clé API.

Source : https://openpaye.co/docs/acces-api

OpenPaye publie également des listes de codes nécessaires aux interfaces :
- conventions collectives ;
- emplois conventionnels ;
- types de contrat ;
- types de temps partiel ;
- statuts professionnels ;
- régimes de retraite ;
- cas particuliers ;
- pays.

Source : https://openpaye.co/docs/liste-des-variables

## 6. Absences et éléments variables

OpenPaye permet l'import des absences avec le **matricule** comme clé d'interface et des données telles que :
- motif / code ;
- valeur ;
- date de début ;
- date de fin.

Source : https://openpaye.co/docs/importer-les-absences

Le logiciel sait valoriser les absences et appliquer des règles de maintien de salaire conventionnel ou légal. Sa propre documentation signale toutefois certains cas non pris en charge, notamment certaines comparaisons légales sur un arrêt prolongé couvrant plusieurs bulletins.

Source : https://openpaye.document360.io/docs/comment-g%C3%A9rer-le-maintien-de-salaire

Cela renforce l'intérêt d'un historique RH complet côté Teamworks sans tenter d'y refaire le calcul de paie.

## 7. Identifiants et table de correspondance à prévoir

Une future interface ne doit pas tenter de retrouver un salarié uniquement par nom/prénom.

Teamworks devrait conserver une correspondance technique explicite, par exemple :

```text
openpaye_employee_id
openpaye_contract_id
openpaye_matricule
openpaye_ccn_code             # 2511
openpaye_conventional_job_code
last_sync_at
sync_hash
sync_status
last_sync_error
```

Le **matricule** doit être stable et unique dans le périmètre de synchronisation.

Le numéro de contrat mérite également une stratégie stable : OpenPaye précise qu'un numéro de contrat n'est plus modifiable après sa création.

Source : https://openpaye.co/docs/remplir-les-fiches-contrats

## 8. Point restant à valider avant codage réel

La documentation publique confirme l'existence des « emplois conventionnels » et leurs codes, mais l'étude n'a pas encore permis d'obtenir la table détaillée des codes OpenPaye correspondant à la CCNS Sport.

Il faut donc vérifier, avec un compte/API OpenPaye :
- si les emplois conventionnels Sport correspondent directement à G1…G8 ;
- s'ils contiennent des subdivisions supplémentaires ;
- quel identifiant technique doit être envoyé à l'API.

Ce point bloque uniquement le **raccordement réel**, pas la conception de l'adaptateur.

## 9. Sens de synchronisation recommandé

### Phase initiale

**Teamworks → OpenPaye**, avec lecture de contrôle depuis OpenPaye lorsque l'API le permet.

Ne pas commencer par une synchronisation bidirectionnelle d'écriture.

Flux cible :

1. la donnée RH est créée/modifiée dans Teamworks ;
2. Teamworks exécute ses contrôles ;
3. une anomalie bloquante interdit l'envoi comme donnée « validée » ;
4. les données validées sont transformées dans le format OpenPaye ;
5. OpenPaye reçoit salarié/contrat/variables/absences ;
6. l'identifiant distant et l'état de synchronisation sont conservés ;
7. un contrôle de rapprochement peut ensuite signaler les divergences.

États recommandés :

```text
BROUILLON
A_CONTROLER
PRET_A_TRANSMETTRE
SYNCHRONISE
ERREUR_SYNCHRONISATION
A_RAPPROCHER
```

Une réponse HTTP positive d'OpenPaye ne doit jamais transformer automatiquement une anomalie RH Teamworks en conformité.

## 10. Sécurité

L'API manipule des données RH très sensibles. L'intégration devra respecter au minimum :
- HTTPS exclusivement ;
- clé API hors des journaux ;
- stockage du secret dans un mécanisme sécurisé, et non en clair dans une table métier ;
- masquage du NIR et des coordonnées bancaires dans les traces ;
- journal d'audit des transmissions ;
- envoi du strict nécessaire ;
- permissions séparées entre consultation RH et administration de l'interface paie.

## 11. Scénarios de recette à prévoir

Avant toute utilisation réelle, l'adaptateur devra être testé au minimum sur :

1. CDI G3 à temps plein ;
2. G1 à 10 h/semaine avec contrôle du minimum majoré ;
3. G7 avec minimum annuel ;
4. CDD avec motif et date de fin ;
5. renouvellement de CDD ;
6. changement de classification G2 → G3 ;
7. salarié à temps partiel avec heures complémentaires ;
8. CEE titulaire BAFA ;
9. CEE stagiaire BAFA ;
10. absence en jours ;
11. absence en heures ;
12. changement de salaire ;
13. doublon de matricule ;
14. rejet API ;
15. rapprochement entre minimum attendu Teamworks et paie calculée OpenPaye.

## 12. Décision architecturale proposée

Ne pas développer un moteur de paie complet dans Teamworks-CCNS.

Conserver dans Teamworks tout ce qui permet à l'employeur de répondre aux questions :

- « Ai-je choisi le bon contrat ? »
- « Le groupe CCNS est-il cohérent avec le poste ? »
- « Le salaire proposé est-il conforme ? »
- « Le temps partiel et ses avenants sont-ils licites ? »
- « Le CEE reste-t-il dans ses plafonds ? »
- « Une prime ou une reclassification doit-elle être examinée ? »
- « Les données RH transmises à la paie sont-elles cohérentes ? »

Laisser à OpenPaye les questions :

- « Quel bulletin faut-il calculer ce mois-ci ? »
- « Quelles cotisations et assiettes appliquer ? »
- « Quel prélèvement à la source appliquer ? »
- « Quelle DSN produire et transmettre ? »
- « Quel montant exact porter sur le bulletin après toutes les règles de paie ? »

Cette séparation réduit fortement le risque réglementaire tout en conservant la valeur spécifique du moteur RH/CCNS de Teamworks.
