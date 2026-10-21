# Effectifs et ETP — moteur de calcul, lot 1

**Chantier CCNS/extensions.** Premier lot métier pur sur `master`, sans modification d'interface et sans migration de base. Les résultats ne constituent **pas** une déclaration réglementaire.

## Distinctions essentielles

- **ETP contractuel** : part de temps plein mesurée par l'horaire contractuel et les dates. Une quotité de 17,5 h sur 35 h représente 0,5 ETP avant prorata de présence.
- **Personnes physiques proratisées** : personnes présentes sur chaque jour, indépendamment de leur horaire. Ce n'est pas un ETP.
- **Effectif moyen annuel réglementaire** : doit être calculé selon les règles propres au dispositif (population, contrats exclus, contrats de remplacement, périodes de référence, arrondis, et traitement des absences), et rapproché du résultat Urssaf/DSN.

Un seul référentiel ne saurait couvrir automatiquement l'Urssaf, la formation (part légale ou conventionnelle, OPCO), la CAF, les collectivités et les autres partenaires.

## Périmètre développé (simulation uniquement)

- `domain/effectifs.py` : profils versionnés, douze mois, prorata des jours calendaires et du temps contractuel, détails mensuels par salarié, exclusions, anomalies bloquantes, affichage tronqué au centième.
- `infrastructure/persistence/teamworks_etp_adapter.py` : adaptation en lecture seule de `CcnsContratRecord`, depuis `CcnsDataReader.lire_contrats()`. Chaque comparaison de quatre profils lit la base **une seule fois**.
- Quatre simulations : CEE oui/non × apprentis oui/non. Elles sont explicitement **non déclarables** et ne sont pas des profils Urssaf ou Afdas certifiés.
- Le moteur accepte d'autres catégories (contrats de professionnalisation notamment), deux modes de dénominateur annuel et une mesure « personnes ».
- Aucune remontée automatique des bulletins, DSN, absences ou contrats d'avenants dans ce lot.

## Limites et contrôles préalables à l'usage déclaratif

1. Vérifier les textes par dispositif et par exercice : exclusions des apprentis, CEE, contrats pro, CDD de remplacement ; méthode des effectifs mensuels, diviseur, date de prise en compte, plafonnement, arrondis.
2. Le lecteur historique ne fournit que `contrats_types.nom` (libellé libre), `date_debut`, `date_fin` et `temps_hebdo`. Les libellés inconnus, dates illisibles ou horaires incorrects génèrent des **anomalies bloquantes**.
3. Les CEE peuvent être définis en jours, et non en heures hebdomadaires. Aucun ETP de CEE n'est inventé quand l'horaire source manque. Leur mode de valorisation devra être défini **par référentiel**.
4. Absences, congés, remplacement, avenants historisés, statut signé/brouillon, multi-contrats et horaires modulés exigent un enrichissement de lecture. Un profil excluant les CDD de remplacement ne peut pas être validé sans un indicateur de remplacement.
5. Tout chevauchement de contrats d'un même salarié est plafonné à une unité pour la simulation journalière **et signalé comme anomalie bloquante** en attendant qualification. Un dépassement mensuel n'est jamais compensé silencieusement.
6. Le résultat interne `total_brut` n'est pas arrondi. `total_affiche` est tronqué au centième ; cette politique **ne doit pas** être présentée comme universelle.
7. Aucun résultat n'est `declarable` tant qu'un profil réglementaire vérifié, versionné et doté de sources n'est pas fourni ET qu'il n'y a pas d'anomalies bloquantes.

## Qualification et suites

- Tests ciblés : `python -m pytest -q tests/test_effectifs.py`.
- Prochain lot : règles Urssaf/EMA vérifiées et profils Afdas, traitement des absences et avenants, définition des CEE, exports CSV/PDF justifiés, historisation des sources/règles, puis intégration d'un écran **RH → Effectifs et ETP** sur `wx/master` et `qt/master` sans duplication du calcul.
- Première contre-qualification métier : année 2025 sur copie de la base PMSL, rapprochement Urssaf et données salariales. **Ne jamais committer de bulletins, noms ou montants individuels.**
