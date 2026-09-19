# Référence des mots-clés

Cette page référence les **47 mots-clés standard distincts** exposés par le moteur de publipostage wx actuel (`teamworks/Utils/UTILS_Publipostage_donnees.py` et `teamworks/Dlg/DLG_Publiposteur*.py`), reconstruite et vérifiée directement depuis le code — pas recopiée de l'ancien Wiki. La syntaxe est exactement `{MOTCLE}`.

!!! warning "Deux flux de publipostage légèrement différents"
    - Le **flux générique** (sélection de personnes/candidats/candidatures/contrats puis **Courrier**, via `DLG_Publiposteur_Choix` → `DLG_Publiposteur`) expose les 47 mots-clés ci-dessous.
    - Le flux **« Imprimer un document »** depuis la fiche contrat (`DLG_Publiposteur_contrat`) expose les mêmes mots-clés **plus** l'alias historique `{BRUTJOUR}` et, indirectement, la [couche moderne RH](#couche-moderne-rh) — voir plus bas.

## Index alphabétique

[`{ADRESSERESID}`](#publipostage-adresseresid) · [`{AFFECTATIONS}`](#publipostage-affectations) · [`{AGE}`](#publipostage-age) · [`{BAREMECEE}`](#publipostage-baremecee) · [`{BRUTJOUR}`](#publipostage-brutjour) · [`{CIVILITE}`](#publipostage-civilite) · [`{CLASSIFICATION}`](#publipostage-classification) · [`{CONFORMITEREMUNERATION}`](#publipostage-conformiteremuneration) · [`{CONVENTION}`](#publipostage-convention) · [`{CPNAISS}`](#publipostage-cpnaiss) · [`{CPRESID}`](#publipostage-cpresid) · [`{DATEDEBUT}`](#publipostage-datedebut) · [`{DATEDEPOT}`](#publipostage-datedepot) · [`{DATEFIN}`](#publipostage-datefin) · [`{DATENAISS}`](#publipostage-datenaiss) · [`{DATEREPONSE}`](#publipostage-datereponse) · [`{DECISION}`](#publipostage-decision) · [`{DISPONIBILITES}`](#publipostage-disponibilites) · [`{DUREEHEBDO}`](#publipostage-dureehebdo) · [`{EMAILS}`](#publipostage-emails) · [`{ESSAI}`](#publipostage-essai) · [`{FAX}`](#publipostage-fax) · [`{FONCTIONS}`](#publipostage-fonctions) · [`{GROUPECCNS}`](#publipostage-groupeccns) · [`{MEMO}`](#publipostage-memo) · [`{MINIMUMCCNS}`](#publipostage-minimumccns) · [`{MINIMUMCEE}`](#publipostage-minimumcee) · [`{MINIMUMRETENU}`](#publipostage-minimumretenu) · [`{MINIMUMSMIC}`](#publipostage-minimumsmic) · [`{NATIONALITE}`](#publipostage-nationalite) · [`{NOM}`](#publipostage-nom) · [`{NOMJFILLE}`](#publipostage-nomjfille) · [`{NUMSECU}`](#publipostage-numsecu) · [`{OFFREDEMPLOI}`](#publipostage-offredemploi) · [`{PAYSNAISS}`](#publipostage-paysnaiss) · [`{PRENOM}`](#publipostage-prenom) · [`{QUALIFICATIONCEE}`](#publipostage-qualificationcee) · [`{QUALIFICATIONS}`](#publipostage-qualifications) · [`{SALAIREBRUTMENSUEL}`](#publipostage-salairebrutmensuel) · [`{SITUATION}`](#publipostage-situation) · [`{TELEPHONES}`](#publipostage-telephones) · [`{TYPECONTRAT}`](#publipostage-typecontrat) · [`{TYPEDEPOT}`](#publipostage-typedepot) · [`{TYPEREPONSE}`](#publipostage-typereponse) · [`{VALEURPOINT}`](#publipostage-valeurpoint) · [`{VILLENAISS}`](#publipostage-villenaiss) · [`{VILLERESID}`](#publipostage-villeresid)

Voir la [matrice des contextes](contextes.md) pour la lecture inverse « je rédige tel document, quels mots-clés puis-je utiliser ? ».

## Compatibilité et comportement

- **Teamword**, **Microsoft Word** (COM) et **LibreOffice Writer** (UNO) reçoivent la même recherche `{MOTCLE}` sensible à la casse, exécutée séparément dans chacun des trois moteurs (`DLG_Publiposteur.py`).
- **Une balise inconnue n'est jamais recherchée** : seuls les mots-clés effectivement présents dans les données du document sont substitués, donc un `{TRUC}` qui n'existe pas reste visible tel quel.
- Une valeur absente devient généralement une chaîne vide, **sauf** pour `NOM`, `PRENOM`, `CIVILITE`, `NOMJFILLE`, `ADRESSERESID`, `VILLERESID`, `VILLENAISS`, `NUMSECU` et `MEMO`, qui recopient la valeur brute de la base sans normalisation : si la colonne correspondante est `NULL` en base, le comportement exact du remplacement dépend du moteur de fusion (Word/Writer/Teamword) et n'a pas été vérifié en recette — **à confirmer en recette fonctionnelle**.
- `ESSAI` n'est jamais vide : il vaut `"0"` par défaut si la colonne est `NULL`.
- Les clés internes commençant par `_` servent aux liaisons internes et ne sont pas des mots-clés de modèle.
- Il n'existe **aucun contexte** `présences`, `planning`, `frais` ou `dpae` dans le moteur audité — recherche exhaustive négative.

!!! danger "Modèles d'exemple avec balises non résolues"
    Les modèles fournis « Contrat à durée déterminée - Exemple.twd » et « Contrat d'engagement éducatif - Exemple.twd » (`teamworks/Static/Documents/`) contiennent `{NBREJOURS}` et `{REPARTITION}`, qui ne correspondent à **aucun** mot-clé du moteur ni à un champ personnalisé pré-configuré. Sur une installation neuve, ces deux balises resteront visibles telles quelles tant qu'un administrateur n'aura pas créé un [champ personnalisé de contrat](#champs-personnalises) portant exactement ce nom.

## Compatibilité historique

`{CLASSIFICATION}` et `{VALEURPOINT}` restent disponibles pour les anciens contrats/modèles (compatibilité historique, sans lien avec le contrôle CCNS moderne).

Le champ `BRUTMENS` (avec `HEBDO` et `ANNUEL`) n'est **pas** un alias de `{SALAIREBRUTMENSUEL}` : c'est un champ de contrat historique, masqué automatiquement de la liste des compléments optionnels lorsque la convention CCNS est sélectionnée (`DLG_Creation_contrat.py`), sans recopie de valeur.

Le seul alias réellement implémenté et testé est `{BRUTJOUR}` → `{BAREMECEE}` (voir [référence détaillée](#publipostage-brutjour)).

## Couche moderne RH {#couche-moderne-rh}

Une couche additive plus récente (`domain/documents/merge_context.py`, `teamworks/Utils/UTILS_Documents_RH.py`, `teamworks/Utils/UTILS_Organisation.py`) ajoute des clés préfixées, **en plus** des 47 mots-clés standard, mais **uniquement dans le flux « Imprimer un document » de la fiche contrat** (`DLG_Publiposteur_contrat`) — le sélecteur générique (`DLG_Publiposteur_Choix`) ne les câble pas.

| Préfixe | Nombre de clés | Origine | Exemples |
|---|---|---|---|
| `STRUCTURE_*` | 23 | Profil de l'association/employeur (`UTILS_Organisation.BuildProfilPublipostage`) | `STRUCTURE_RAISON_SOCIALE`, `STRUCTURE_SIRET`, `STRUCTURE_REPRESENTANT_LEGAL` |
| `SALARIE_*` | 9 | Doublon simplifié des données personne, préfixé | `SALARIE_NOM`, `SALARIE_ADRESSE`, `SALARIE_TELEPHONES` |
| `CONTRAT_*` | 8 | Doublon simplifié des données contrat, préfixé | `CONTRAT_DATE_DEBUT`, `CONTRAT_GROUPE_CCNS` |

Ces clés ne s'écrasent jamais avec les mots-clés historiques (elles sont ajoutées par `setdefault`, jamais en remplacement). Un catalogue de types de documents RH plus large (`domain/documents/catalog.py` — dispense mutuelle, attestation d'emploi, autorisation parentale mineur, certificat de travail...) existe côté domaine mais **n'a aucun écran wx qui l'utilise à ce jour** : ne le présentez pas comme disponible.

## Champs personnalisés {#champs-personnalises}

Deux systèmes de champs personnalisés existent, distincts et non interchangeables :

1. **Champs de contrat** (`contrats_champs`/`contrats_valchamps`) : configurés via **Paramétrage > Contrats > Les champs de contrats** (`DLG_Config_champs_contrats.py`), saisis via `DLG_Saisie_champs_contrats.py`. La valeur est stockée **par contrat** et fusionnée automatiquement — disponible dans le flux générique comme dans le flux page-contrat.
2. **Champs de publipostage** (`publipostage_champs`) : créés depuis l'étape de vérification de l'assistant (`DLG_Saisie_champs_publipostage.py`), disponibles pour personne/candidat/candidature/contrat. Contrairement aux champs de contrat, **la valeur n'est pas stockée par enregistrement** : une valeur par défaut s'applique à tout le lot de documents généré, à corriger manuellement document par document dans la grille « Vérification des données » si besoin.

Dans les deux systèmes, le mot-clé doit être unique, en MAJUSCULES, alphanumérique, sans accents ni espaces. Cette documentation ne peut pas lister leurs noms : ils dépendent de votre base. Pour retrouver le mot-clé exact, ouvrez la grille **Vérification des données du document** ou le paramétrage du champ concerné. Ne fabriquez jamais une balise à partir d'un libellé.

## Référence détaillée

### Contexte Individu (18 mots-clés)

Disponibles pour une **Personne**, et hérités tels quels par le **Contrat** (données du titulaire) et, en partie, par le **Candidat**/la **Candidature** — voir la [matrice des contextes](contextes.md).

<a id="publipostage-civilite"></a>
#### `{CIVILITE}`
Civilité enregistrée (`personnes.civilite`). Valeur brute, non normalisée si `NULL`.

<a id="publipostage-nom"></a>
#### `{NOM}`
Nom de famille (`personnes.nom`). Valeur brute.

<a id="publipostage-nomjfille"></a>
#### `{NOMJFILLE}`
Nom de naissance/jeune fille (`personnes.nom_jfille`). Valeur brute.

<a id="publipostage-prenom"></a>
#### `{PRENOM}`
Prénom (`personnes.prenom`). Valeur brute.

<a id="publipostage-datenaiss"></a>
#### `{DATENAISS}`
Date de naissance, formatée en date française (`UTILS_Dates.DateEngFr`). Vide si non renseignée.

<a id="publipostage-age"></a>
#### `{AGE}`
Âge calculé depuis `DATENAISS`. Vide si aucune date de naissance. *(Côté Candidat, l'âge est d'abord lu directement en base s'il est renseigné, sinon calculé — logique légèrement différente.)*

<a id="publipostage-cpnaiss"></a>
#### `{CPNAISS}`
Code postal de naissance, zéro-paddé sur 5 caractères. Vide si non renseigné.

<a id="publipostage-villenaiss"></a>
#### `{VILLENAISS}`
Ville de naissance. Valeur brute.

<a id="publipostage-paysnaiss"></a>
#### `{PAYSNAISS}`
Pays de naissance, résolu par jointure sur la table `pays`. Vide si l'identifiant est absent, invalide ou introuvable.

<a id="publipostage-nationalite"></a>
#### `{NATIONALITE}`
Nationalité, résolue par la même jointure que `PAYSNAISS`. Vide dans les mêmes conditions.

<a id="publipostage-numsecu"></a>
#### `{NUMSECU}`
Numéro de sécurité sociale (`personnes.num_secu`). Valeur brute. **Donnée sensible : ne jamais l'utiliser dans un exemple public.**

<a id="publipostage-adresseresid"></a>
#### `{ADRESSERESID}`
Adresse de résidence. Valeur brute.

<a id="publipostage-cpresid"></a>
#### `{CPRESID}`
Code postal de résidence, zéro-paddé sur 5 caractères. Vide si non renseigné.

<a id="publipostage-villeresid"></a>
#### `{VILLERESID}`
Ville de résidence. Valeur brute.

<a id="publipostage-situation"></a>
#### `{SITUATION}`
Situation familiale, résolue par jointure sur `situations`. Vide si aucune ligne correspondante.

<a id="publipostage-telephones"></a>
#### `{TELEPHONES}`
Téléphones (catégories Fixe/Mobile de `coordonnees`) concaténés par `", "`. Vide si aucun.

<a id="publipostage-emails"></a>
#### `{EMAILS}`
Emails (catégorie Email de `coordonnees`) concaténés. Vide si aucun. Sert aussi de destinataire pour l'envoi mail direct depuis Teamword.

<a id="publipostage-fax"></a>
#### `{FAX}`
Numéros de fax concaténés. Vide si aucun.

### Contexte Candidat (2 mots-clés propres, + 11 hérités d'Individu)

Le Candidat reprend un sous-ensemble de 11 mots-clés Individu (`CIVILITE`, `NOM`, `PRENOM`, `DATENAISS`, `AGE`, `ADRESSERESID`, `CPRESID`, `VILLERESID`, `TELEPHONES`, `FAX`, `EMAILS`) — sans `NOMJFILLE`, `CPNAISS`, `VILLENAISS`, `PAYSNAISS`, `NATIONALITE`, `NUMSECU`, `SITUATION`.

<a id="publipostage-qualifications"></a>
#### `{QUALIFICATIONS}`
Diplômes/qualifications du candidat, concaténés (`types_diplomes`/`diplomes_candidats`). Vide si aucun.

<a id="publipostage-memo"></a>
#### `{MEMO}`
Mémo libre du candidat (`candidats.memo`). Valeur brute.

### Contexte Candidature (9 mots-clés propres)

Une candidature charge d'abord les mots-clés de la **Personne** liée si `IDpersonne` est renseigné, sinon ceux du **Candidat**, puis ajoute :

<a id="publipostage-datedepot"></a>
#### `{DATEDEPOT}`
Date de dépôt de la candidature, formatée.

<a id="publipostage-typedepot"></a>
#### `{TYPEDEPOT}`
Canal/type de dépôt, résolu depuis une liste de libellés codée dans l'application.

<a id="publipostage-offredemploi"></a>
#### `{OFFREDEMPLOI}`
Intitulé de l'offre liée, ou « Candidature spontanée » si aucune offre n'est rattachée.

!!! note "Champs d'offre non exposés"
    Le code calcule aussi `OFFRE_DATEDEBUT`, `OFFRE_DATEFIN`, `OFFRE_DETAIL` et `OFFRE_REFERENCE_ANPE` en interne, mais **aucun n'est exposé** comme mot-clé de publipostage (code mort côté candidature) — ne les utilisez pas dans un modèle.

<a id="publipostage-disponibilites"></a>
#### `{DISPONIBILITES}`
Périodes de disponibilité assemblées. Vide si aucune.

<a id="publipostage-fonctions"></a>
#### `{FONCTIONS}`
Fonctions souhaitées de la candidature. Vide si aucune.

<a id="publipostage-affectations"></a>
#### `{AFFECTATIONS}`
Affectations souhaitées de la candidature. Vide si aucune.

<a id="publipostage-decision"></a>
#### `{DECISION}`
Décision de candidature, résolue en libellé utilisateur.

<a id="publipostage-datereponse"></a>
#### `{DATEREPONSE}`
Date de réponse. Renseignée uniquement si une réponse a été enregistrée, vide sinon.

<a id="publipostage-typereponse"></a>
#### `{TYPEREPONSE}`
Canal/type de réponse. Mêmes conditions que `DATEREPONSE`.

### Contexte Contrat (17 mots-clés propres, + 18 hérités d'Individu via le titulaire)

<a id="publipostage-datedebut"></a>
#### `{DATEDEBUT}`
Date de début du contrat, formatée.

<a id="publipostage-datefin"></a>
#### `{DATEFIN}`
Date de fin du contrat lorsqu'elle existe.

<a id="publipostage-classification"></a>
#### `{CLASSIFICATION}`
Classification historique, si `IDclassification` est renseigné. Compatibilité historique — vide sinon.

<a id="publipostage-typecontrat"></a>
#### `{TYPECONTRAT}`
Type/intitulé du contrat, résolu depuis `contrats_types`.

<a id="publipostage-valeurpoint"></a>
#### `{VALEURPOINT}`
Valeur du point historique, formatée « X € ». Compatibilité historique.

<a id="publipostage-essai"></a>
#### `{ESSAI}`
Indicateur de période d'essai (`contrats.essai`, casté en texte). **Vaut `"0"` par défaut**, jamais vide.

<a id="publipostage-convention"></a>
#### `{CONVENTION}`
Code/libellé de convention (`contrats.convention_code`).

<a id="publipostage-groupeccns"></a>
#### `{GROUPECCNS}`
Groupe CCNS du contrat (`contrats.ccns_group`) lorsqu'il est renseigné.

<a id="publipostage-qualificationcee"></a>
#### `{QUALIFICATIONCEE}`
Qualification/statut CEE, résolu depuis une table de libellés.

<a id="publipostage-dureehebdo"></a>
#### `{DUREEHEBDO}`
Durée hebdomadaire du contrat, formatée « X h ».

<a id="publipostage-salairebrutmensuel"></a>
#### `{SALAIREBRUTMENSUEL}`
Salaire brut mensuel (`contrats.gross_monthly_salary`), formaté « X,XX € ».

<a id="publipostage-minimumccns"></a>
#### `{MINIMUMCCNS}`
Minimum CCNS calculé pour ce contrat (grille de groupe, temps de travail, majoration temps partiel) — voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md#controle-ccns). Vide si le calcul n'est pas possible (groupe/date/convention manquants).

<a id="publipostage-minimumsmic"></a>
#### `{MINIMUMSMIC}`
Minimum SMIC applicable, proratisé selon la durée hebdomadaire (sans majoration temps partiel, contrairement au CCNS). Vide si non calculable.

<a id="publipostage-minimumretenu"></a>
#### `{MINIMUMRETENU}`
Le plus élevé entre `MINIMUMCCNS` et `MINIMUMSMIC` (source indiquée : CCNS, SMIC ou égalité). Vide si non calculable.

<a id="publipostage-conformiteremuneration"></a>
#### `{CONFORMITEREMUNERATION}`
Résultat textuel du contrôle de rémunération (« CONFORME », « NON CONFORME — manque X € », ou « Contrôle annuel requis » pour les groupes à minimum annuel). Ce n'est pas une certification juridique.

<a id="publipostage-baremecee"></a>
#### `{BAREMECEE}`
Barème CEE employeur applicable (qualification + date d'effet), si configuré dans **Paramétrage > Barèmes CEE**. Vide sinon.

<a id="publipostage-minimumcee"></a>
#### `{MINIMUMCEE}`
Minimum légal journalier CEE (SMIC horaire métropole × coefficient réglementaire en vigueur à la date du contrat). Vide si non calculable.

<a id="publipostage-brutjour"></a>
#### `{BRUTJOUR}`
**Alias historique de `{BAREMECEE}`**, disponible **uniquement** dans le flux « Imprimer un document » depuis la fiche contrat, et **seulement si** `QUALIFICATIONCEE` et `BAREMECEE` sont tous deux non vides pour ce contrat. Absent du sélecteur générique de publipostage. C'est le 47ᵉ mot-clé du décompte total.

## Voir aussi

[Contextes d'utilisation](contextes.md) · [Exemples](exemples.md) · [Documents et publipostage](../utilisation/documents.md) · [Éditeur interne (Teamword)](../utilisation/editeur.md) · [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md)
