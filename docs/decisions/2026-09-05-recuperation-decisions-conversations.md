# Sauvegarde des décisions fonctionnelles issues des conversations

Date de sauvegarde : 2026-09-05

> Ce document est une sauvegarde de décisions et besoins fonctionnels validés dans les conversations du projet avant leur nettoyage. Il sert à éviter qu'une suppression de conversation fasse perdre une décision non encore matérialisée dans le code. Il ne signifie pas que toutes les fonctions décrites sont déjà implémentées.

## 1. Portail / accueil / continuité associative

### Finalité

Le futur **Portail** doit remplacer Connecthys avec des fonctionnalités qui dépassent les possibilités du Connecthys actuel.

L'objectif n'est pas seulement une nouvelle interface : le système doit conserver la connaissance institutionnelle et opérationnelle de l'association afin qu'elle ne dépende pas d'une seule personne. En particulier, si Franck quitte l'association, les informations nécessaires à la continuité doivent rester accessibles dans le système selon les droits appropriés.

### Éléments fonctionnels à conserver

L'accueil / Portail doit pouvoir regrouper ou donner accès à :

- un flux d'actualités / RSS utile à l'activité ;
- les échéances de conformité, notamment les documents salariés et le DUERP ;
- un indicateur ETP sur une période, en excluant les CEE ;
- un annuaire de contacts professionnels et institutionnels ;
- les informations utiles concernant le bureau / CA ;
- les collectivités partenaires ;
- le conseiller ou la conseillère CTG ;
- un mémento protégé par mot de passe pour les informations qui le nécessitent ;
- une synchronisation adaptée avec le téléphone ;
- la possibilité pour Cindy d'ajouter un salarié via le Portail.

### Annuaire institutionnel identifié

Les contacts professionnels à pouvoir structurer comprennent notamment :

- SDJES35 ;
- PST35 ;
- France Travail ;
- URSSAF ;
- DREETS / DIRECCTE selon la dénomination pertinente ;
- assurance ;
- prévoyance ;
- COSMOS ou autre syndicat employeur du sport ;
- CAF ;
- collectivités partenaires ;
- interlocuteur CTG.

### Droits et synchronisation

- Tous les contacts professionnels ne doivent pas être diffusés indistinctement à tous les salariés.
- Le coordinateur sportif ne doit notamment pas recevoir automatiquement l'ensemble de l'annuaire professionnel/institutionnel.
- L'équipe utilise Signal pour ses échanges.
- Il n'est pas prévu d'imposer CardDAV sur les téléphones personnels non professionnels.
- Les droits du Portail doivent donc être pensés par rôle et par besoin, et non comme une réplication globale de l'annuaire.

## 2. Connecthys et hébergement

### Connecthys

Connecthys a vocation à être remplacé par le Portail. Les nouvelles fonctions envisagées ne doivent pas être contraintes par les possibilités du Connecthys existant.

### 02switch

02switch héberge actuellement :

- les courriels ;
- le WordPress.

Un éventuel rapatriement futur de ces services reste **une question ouverte**, et non une décision validée.

Aucune documentation ne doit transformer cette hypothèse en décision d'hébergement.

## 3. Documents RH et publipostage

### Principe

Les documents RH doivent s'appuyer sur des modèles Microsoft Office et un mécanisme de sélection / publipostage adapté aux besoins RH.

Les travaux déjà suivis dans GitHub (#312, #313 et la récupération #383) constituent la base technique connue. Les besoins ci-dessous doivent être vérifiés contre leur implémentation avant de considérer le sujet comme complètement couvert.

### Documents identifiés

Le périmètre évoqué comprend notamment :

- attestations d'emploi ;
- autorisations de travail pour les mineurs ;
- attestations d'expérience ;
- documents liés aux contrats et au parcours salarié ;
- lorsque pertinent, documents ou données nécessaires aux démarches France Travail.

Cette liste est fonctionnelle et n'affirme pas que chacun de ces documents est déjà implémenté.

### Modèles et champs

- Les modèles sont des documents Office destinés au publipostage.
- Les données employeur doivent provenir d'une source structurée plutôt que d'être dupliquées manuellement dans chaque modèle.
- Lorsqu'une donnée de publipostage est absente, le document généré ne doit pas laisser apparaître un marqueur technique disgracieux de type `<mot_cle>`.
- Si une valeur manque et doit pouvoir être complétée humainement, le résultat doit laisser un emplacement propre et remplissable.
- Les frontières entre données salarié, données employeur, contrat et document doivent rester explicites afin d'être réutilisables lors de la migration Qt.

## 4. Règle documentaire pour la suite

À compter de cette sauvegarde :

1. les conversations ne doivent plus être la seule source d'une décision durable ;
2. toute décision validée doit être matérialisée dans GitHub : documentation, issue, PR, test ou code selon sa nature ;
3. une conversation ancienne ne doit pas prévaloir sur une décision Git plus récente ;
4. les hypothèses doivent être explicitement distinguées des décisions ;
5. les besoins fonctionnels non encore implémentés restent des besoins, et ne doivent pas être décrits comme des fonctions existantes.

## 5. Points à requalifier ultérieurement

Cette sauvegarde permet de supprimer les conversations sans perdre les éléments connus, mais les points suivants nécessitent encore une confrontation au dépôt avant développement :

- couverture exacte de #312 / #313 / #383 par rapport aux besoins Documents RH ci-dessus ;
- modèle de droits du Portail et de l'annuaire ;
- source de vérité des contacts institutionnels ;
- mécanisme exact de synchronisation téléphone ;
- périmètre et sécurité du mémento protégé ;
- définition fonctionnelle exacte de l'indicateur ETP hors CEE ;
- modalités de remplacement terrain de Connecthys ;
- éventuelle évolution de l'hébergement 02switch, qui reste non décidée.
