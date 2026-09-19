# Exemples

Ces exemples sont fictifs et ne contiennent aucune donnée personnelle réelle. Ils utilisent uniquement des mots-clés confirmés dans le code — voir la [référence des mots-clés](mots-cles.md) pour le détail de chacun.

## Contexte Individu — courrier simple

```text
Bonjour {CIVILITE} {NOM},

Nous vous confirmons votre adresse enregistrée :
{ADRESSERESID}, {CPRESID} {VILLERESID}

Cordialement,
```

## Contexte Contrat — confirmation d'embauche

```text
{CIVILITE} {PRENOM} {NOM},

Votre contrat ({TYPECONTRAT}) débute le {DATEDEBUT} et se termine le {DATEFIN}.
Durée hebdomadaire : {DUREEHEBDO}
Salaire brut mensuel : {SALAIREBRUTMENSUEL}

Contrôle de rémunération : {CONFORMITEREMUNERATION}
(Minimum retenu : {MINIMUMRETENU})
```

!!! note
    `{MINIMUMRETENU}` et `{CONFORMITEREMUNERATION}` restent vides si le calcul n'est pas possible (convention, groupe ou date manquants) — voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md).

## Contexte Contrat CEE — engagement éducatif

```text
{CIVILITE} {PRENOM} {NOM},

Qualification CEE : {QUALIFICATIONCEE}
Barème employeur applicable : {BAREMECEE}
Minimum légal journalier CEE : {MINIMUMCEE}
```

!!! warning "`{BRUTJOUR}` uniquement depuis la fiche contrat"
    L'alias `{BRUTJOUR}` (= `{BAREMECEE}`) n'est disponible que si ce document est généré depuis le bouton **Imprimer un document** de l'onglet Contrats, pas depuis le sélecteur généraliste. Préférez `{BAREMECEE}` dans un modèle destiné aux deux flux.

## Contexte Candidature — réponse à candidature

```text
{CIVILITE} {NOM} {PRENOM},

Concernant votre candidature déposée le {DATEDEPOT} pour {OFFREDEMPLOI} :
Décision : {DECISION}
```

## Contexte Candidat — accusé de réception

```text
Bonjour {PRENOM},

Nous avons bien reçu votre candidature. Qualifications enregistrées :
{QUALIFICATIONS}
```

## Voir aussi

[Référence des mots-clés](mots-cles.md) · [Contextes d'utilisation](contextes.md) · [Documents et publipostage](../utilisation/documents.md)
