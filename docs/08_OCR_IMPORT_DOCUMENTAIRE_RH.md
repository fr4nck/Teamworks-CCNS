# OCR local et lecture des documents RH

**Statut : piste fonctionnelle, hors feuille de route à ce stade**  
**Date : 27 août 2026**

> Ce document ne crée aucun lot `TW-*` et ne modifie pas les priorités de `ROADMAP.md`. Il conserve le cadrage d’un futur assistant de lecture documentaire RH.

## 1. Objectif

La partie **Documents** du dossier salarié doit pouvoir exploiter les pièces déjà importées dans Teamworks pour aider à compléter et maintenir le dossier RH.

Le principe cible est :

`Document déjà attaché au salarié -> lecture texte/OCR -> reconnaissance -> extraction -> comparaison avec le dossier -> validation humaine -> écriture`

Il ne doit donc pas être nécessaire de réimporter un document pour l’analyser.

## 2. Fonction dans l’onglet Documents

Chaque document attaché au salarié pourra proposer une action **« Lire ce document »**.

L’action :

1. utilise directement le texte si le PDF en contient déjà ;
2. sinon lance un OCR local sur le PDF ou l’image ;
3. détermine si possible la famille du document ;
4. extrait les informations pertinentes ;
5. affiche une fenêtre de contrôle ;
6. propose les modifications à appliquer au dossier salarié ;
7. n’écrit aucune donnée sans validation explicite de l’utilisateur.

Une action ultérieure **« Analyser les documents non lus »** pourra traiter en lot les pièces d’un dossier, mais conservera la validation humaine pour les changements proposés.

## 3. Remplir le bon sous-dossier RH

Le moteur ne doit pas considérer la fiche salarié comme un formulaire plat. Une donnée reconnue doit être routée vers le domaine adapté.

Exemples :

| Document | Données susceptibles d’être reconnues | Destination Teamworks |
|---|---|---|
| Pièce d’identité | nom, prénoms, date et lieu de naissance, nationalité, dates de validité | Identité / administratif |
| Diplôme | intitulé, spécialité, organisme, date d’obtention, numéro, éventuelle échéance | Compétences, diplômes et habilitations |
| Carte professionnelle | numéro, activités autorisées, date de délivrance, échéance | Habilitations / obligations professionnelles |
| Contrat de travail | type, dates, durée du travail, fonction, classification, rémunération | Contrat & CCNS |
| Avenant | date d’effet, nouvelle durée, rémunération, fonction, classification | Historique RH / version de contrat |
| Attestation ou justificatif d’absence | type, période, dates utiles | Temps & absences |
| Document d’entrée ou de départ | dates, références, éléments administratifs | Parcours d’arrivée / départ |
| Bulletin ou état de paie | période, rémunération brute, certaines variables | Rapprochement paie, sans transformer Teamworks en logiciel de paie |

Les informations très sensibles ou soumises à des règles particulières de conservation doivent rester protégées par les permissions RH et les règles RGPD.

## 4. Écran de validation

Pour chaque information reconnue, l’utilisateur doit voir au minimum :

- le champ ciblé ;
- la valeur actuellement présente dans Teamworks ;
- la valeur détectée dans le document ;
- le document source ;
- si possible la page ou zone source ;
- un niveau de confiance lorsque le moteur sait le fournir ;
- une action `Appliquer`, `Ignorer` ou `Corriger`.

Aucun écrasement silencieux n’est autorisé.

Lorsqu’une donnée détectée contredit une donnée existante, le système doit présenter le conflit explicitement au lieu de choisir automatiquement.

## 5. Traçabilité

Une donnée validée depuis un document doit pouvoir conserver :

- l’identifiant du document source ;
- la date de lecture ;
- le moteur utilisé ;
- la valeur extraite initialement ;
- la valeur finalement validée ;
- l’utilisateur ayant validé ;
- la date de validation.

Cette provenance est particulièrement importante pour les diplômes, habilitations, dates contractuelles et informations CCNS.

## 6. Choix technique recommandé

### Moteur principal : Tesseract

Tesseract est le candidat de première ligne : libre, mature, utilisable localement, compatible avec le français et sans coût logiciel.

Teamworks doit l’utiliser derrière une interface applicative, par exemple `OCRProvider`, afin de pouvoir remplacer le moteur ultérieurement sans modifier les règles métier.

### Moteur avancé éventuel

Un moteur plus lourd de type docTR peut être évalué ultérieurement pour les photos prises au téléphone, documents inclinés ou mises en page difficiles. Il ne doit pas alourdir le paquet Windows principal tant que le besoin réel n’est pas démontré.

## 7. Sécurité et confidentialité

Par défaut, la lecture doit être **locale** : les documents RH ne sont pas envoyés à un service OCR externe.

Le texte OCR intermédiaire doit suivre les mêmes droits d’accès et règles de conservation que le document source. Il ne doit pas devenir une copie non maîtrisée de données personnelles dans des fichiers temporaires permanents.

Les fichiers temporaires de traitement doivent être supprimés après usage lorsque leur conservation n’est pas nécessaire.

## 8. Architecture fonctionnelle cible

Le module doit rester composé de couches distinctes :

- `DocumentReader` : récupère texte natif ou image à traiter ;
- `OCRProvider` : transforme l’image en texte et positions ;
- `DocumentClassifier` : propose le type de document ;
- `DocumentExtractor` : extrait des valeurs structurées selon le type ;
- `EmployeeFieldMapper` : indique la destination RH de chaque donnée ;
- `DocumentImportReview` : prépare la comparaison avec les données existantes ;
- couche d’écriture RH : applique uniquement les éléments explicitement validés.

Les extracteurs ne doivent contenir aucune écriture directe en base.

## 9. Priorité fonctionnelle proposée

Première cible utile :

1. diplômes et habilitations ;
2. cartes professionnelles ;
3. contrats et avenants ;
4. pièces d’identité et administratif ;
5. justificatifs d’absence ;
6. rapprochement de documents de paie.

L’objectif n’est pas de construire une GED universelle mais de réduire la ressaisie et les erreurs dans le dossier salarié, tout en conservant une validation humaine et une provenance documentaire vérifiable.
