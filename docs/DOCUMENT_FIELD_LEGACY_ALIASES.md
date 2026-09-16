# Alias historiques des champs documentaires

## Objet

Ce document qualifie les tokens Teamword historiques utilisés par les modèles TWD et leur correspondance avec le registre canonique `domain.documents`.

Règle de gouvernance : un token n'est ajouté au registre que lorsque sa source métier, son propriétaire et son sens sont vérifiés dans le code Teamworks. Le nom historique seul ne suffit pas.

## Alias déjà maîtrisés

| Token historique | Clé canonique | Contexte | Source métier vérifiée | Statut |
|---|---|---|---|---|
| `{NOM}` | `SALARIE_NOM` | employee, contract | personne / salarié Teamworks | conservé |
| `{PRENOM}` | `SALARIE_PRENOM` | employee, contract | personne / salarié Teamworks | conservé |
| `{CIVILITE}` | `SALARIE_CIVILITE` | employee, contract | personne / salarié Teamworks | conservé |
| `{DATENAISS}` | `SALARIE_DATE_NAISSANCE` | employee, contract | `personnes.date_naiss` | conservé |
| `{ADRESSERESID}` | `SALARIE_ADRESSE` | employee, contract | `personnes.adresse_resid` | conservé |
| `{CPRESID}` | `SALARIE_CODE_POSTAL` | employee, contract | `personnes.cp_resid` | conservé |
| `{VILLERESID}` | `SALARIE_VILLE` | employee, contract | `personnes.ville_resid` | conservé |
| `{DATEDEBUT}` | `CONTRAT_DATE_DEBUT` | contract | `contrats.date_debut` | conservé |
| `{DATEFIN}` | `CONTRAT_DATE_FIN` | contract | `contrats.date_fin` | conservé |
| `{CLASSIFICATION}` | `CONTRAT_CLASSIFICATION` | contract | classification associée au contrat | conservé |
| `{TYPECONTRAT}` | `CONTRAT_TYPE` | contract | type associé au contrat | conservé |
| `{CONVENTION}` | `CONTRAT_CONVENTION` | contract | `contrats.convention_code` / projection existante | conservé |
| `{GROUPECCNS}` | `CONTRAT_GROUPE_CCNS` | contract | `contrats.ccns_group` | conservé |
| `{DUREEHEBDO}` | `CONTRAT_DUREE_HEBDO` | contract | `contrats.weekly_hours` | conservé |
| `{SALAIREBRUTMENSUEL}` | `CONTRAT_SALAIRE_BRUT_MENSUEL` | contract | `contrats.gross_monthly_salary` | conservé |

## Alias qualifiés pendant l'itération 3

Les cinq entrées suivantes sont ajoutées parce que leur source métier est explicitement produite par `UTILS_Publipostage_donnees`.

| Token historique | Clé canonique | Type | Contextes | Source de vérité | Resolver | Statut |
|---|---|---|---|---|---|---|
| `{CPNAISS}` | `SALARIE_CODE_POSTAL_NAISSANCE` | text | employee, contract | `personnes.cp_naiss` | `rh.employee.birth_postal_code` | actif |
| `{VILLENAISS}` | `SALARIE_VILLE_NAISSANCE` | text | employee, contract | `personnes.ville_naiss` | `rh.employee.birth_city` | actif |
| `{NUMSECU}` | `SALARIE_NUMERO_SECURITE_SOCIALE` | text | employee, contract | `personnes.num_secu` | `rh.employee.social_security_number` | actif |
| `{ESSAI}` | `CONTRAT_DUREE_ESSAI_JOURS` | number | contract | `contrats.essai` | `rh.contract.trial_period_days` | actif |
| `{VALEURPOINT}` | `CONTRAT_VALEUR_POINT` | number | contract | `contrats.valeur_point` -> `valeurs_point.valeur` | `rh.contract.point_value` | actif |

Le registre exprime le **concept**. Le publiposteur historique peut continuer à formater certaines valeurs (par exemple avec une unité ou une devise) avant de les transmettre au contexte de fusion ; ce formatage de compatibilité n'est pas une nouvelle source de vérité.

## Tokens volontairement non canoniques

| Token | Observation | Décision itération 3 |
|---|---|---|
| `{NBREJOURS}` | présent dans les deux modèles de contrat historiques ; aucun producteur courant vérifié dans `UTILS_Publipostage_donnees` | conserver tel quel, non résolu |
| `{REPARTITION}` | présent dans les deux modèles de contrat historiques ; aucun producteur courant vérifié | conserver tel quel, non résolu |
| `{BRUTJOUR}` | l'adaptateur contrat wx le fabrique comme alias de compatibilité `BRUTJOUR = BAREMECEE` pour les CEE lorsque `QUALIFICATIONCEE` et `BAREMECEE` existent | ne pas en faire un concept canonique général ; conserver l'alias legacy dans l'adaptateur |

`{BRUTJOUR}` ne doit notamment pas être renommé automatiquement en « salaire brut journalier » dans le core : la source actuellement vérifiée est un barème CEE applicable, ce qui n'établit pas qu'il représente dans tous les contextes une rémunération contractuelle journalière réelle.

## Dépréciation

Aucun token historique utilisé par le corpus réel n'est supprimé dans cette itération. Les alias reconnus restent acceptés afin de rendre les anciens TWD importables. Une future dépréciation éventuelle devra être précédée d'un inventaire du patrimoine utilisateur hors dépôt.
