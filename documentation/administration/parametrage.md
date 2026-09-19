# Paramétrage

## Préférences d'affichage

Le dialogue **Préférences** (`teamworks/Dlg/DLG_Preferences.py`) regroupe les réglages d'interface, disponibles et confirmés dans le code :

- **Couleur d'accent** du thème ;
- **Apparence** Système / Clair / Sombre ;
- **Échelle de l'interface** (police et mise à l'échelle générale) ;
- section **Maintenance / Diagnostic** : adresse de réception des rapports d'erreurs (voir [Diagnostic et rapports de crash](diagnostic.md)) ;
- accès rapide à **Structure/association…** et **Références administratives RH…**.

!!! note "Redémarrage nécessaire"
    Le dialogue indique explicitement qu'un redémarrage est nécessaire pour appliquer complètement l'apparence et l'échelle choisies.

## Menu Paramétrage (référentiels métier)

Le menu principal **Paramétrage** regroupe les référentiels utilisés par les fiches, les contrats, le recrutement, le planning et la messagerie. Certaines commandes ne prennent leur sens qu'une fois un dossier ouvert.

### Général et accès

- **Enregistrement** ;
- gestion des **Gadgets** de la page d'accueil ;
- **Accès réseau** ;
- **Adresses d'expédition d'Emails** ;
- **Protection par mot de passe**.

### Individus

- questionnaire ;
- types de qualifications ;
- types de pièces ;
- types de situations ;
- pays et nationalités.

### Planning

- catégories de présences.

### Contrats

- classifications historiques ;
- champs de contrats ;
- modèles de contrats ;
- types de contrats ;
- valeurs de points historiques.

Les groupes/barèmes CCNS et CEE modernes possèdent leurs propres écrans d'édition (**Barèmes CEE…**, groupes CCNS), accessibles depuis l'assistant de création de contrat — voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md).

### Recrutement

- protection des entretiens ;
- fonctions ;
- affectations ;
- diffuseurs ;
- offres d'emploi.

### Calendrier

- vacances ;
- jours fériés.

!!! info "Pas de gestion de comptes applicatifs"
    Le code ne fournit pas de groupe générique « Utilisateurs » indépendant. Ne confondez pas **Accès réseau** (connexion MySQL) avec une gestion complète de comptes applicatifs — voir [Utilisateurs et habilitations](utilisateurs.md).

## Paramètres et effets

| Paramètre | Effet vérifié | Portée | Redémarrage nécessaire |
|---|---|---|---|
| Questionnaire | définit les questions proposées dans la fiche | dossier | non observé dans le code |
| Types de qualifications | alimente les qualifications des personnes/candidats | dossier | non observé |
| Types de pièces | alimente les pièces à fournir/recevoir | dossier | non observé |
| Catégories de présences | alimente la saisie des présences | dossier | non observé |
| Types/modèles/champs de contrats | alimente l'assistant et les documents de contrat | dossier | non observé |
| Fonctions/affectations/offres | alimente le recrutement | dossier | non observé |
| Vacances / jours fériés | alimente le calendrier et certaines conditions de sauvegarde | dossier | non observé |
| Accès réseau | configure l'accès au mode réseau/MySQL | connexion/dossier | dépend du changement effectué ; **à confirmer en recette fonctionnelle** |
| Adresse d'expédition Email | fournit les paramètres utilisés par les envois | dossier/configuration | non observé |
| Protection par mot de passe | protège l'ouverture du dossier | dossier | non observé |

## Paramètres mémorisés automatiquement

Teamworks conserve notamment : dernier dossier et dossiers récents, taille de fenêtre, interface MySQL choisie, présentation des listes et plusieurs choix du publipostage (éditeur, modèle, options de sortie).

## Champs personnalisés {#champs-personnalises}

Deux mécanismes sont importants pour les documents :

- les **champs personnalisés de publipostage** enregistrés dans le dossier et gérés depuis l'étape de vérification de l'assistant ;
- les **champs de contrats**, configurés via **Paramétrage > Contrats > Les champs de contrats**, dont le mot-clé est stocké dans le dossier.

Cette documentation ne peut pas lister leurs noms car ils dépendent de votre base. Pour retrouver le mot-clé exact, ouvrez la grille **Vérification des données du document** du publipostage, ou le paramétrage du champ concerné. Ne devinez jamais une balise. Voir [Champs personnalisés](../publipostage/mots-cles.md#champs-personnalises).

## Réseau / MySQL

Les paramètres réseau modifient la façon dont Teamworks ouvre le dossier. Faites une sauvegarde avant toute conversion ou modification sensible. Voir [Données, sauvegardes et MySQL](donnees-sauvegardes.md).

## Points d'attention

- Modifier un référentiel peut changer les choix proposés dans des fiches existantes.
- Les classifications et valeurs de point sont conservées pour compatibilité historique ; elles ne remplacent pas les contrôles CCNS/CEE modernes.
- Les effets visuels immédiats et besoins éventuels de réouverture d'un écran restent **à confirmer en recette fonctionnelle** lorsque le code ne l'impose pas explicitement.

## Voir aussi

[Individus et fiches](../utilisation/individus.md) · [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md) · [Recrutement](../utilisation/recrutement.md) · [Présences et planning](../utilisation/presences-planning.md) · [Référence des mots-clés](../publipostage/mots-cles.md)
