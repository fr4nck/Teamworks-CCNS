# Paramétrage

<a id="parametrage-menu"></a>
## À quoi ça sert ?

Le menu **Paramétrage** regroupe les référentiels utilisés par les fiches, les contrats, le recrutement, le planning et la messagerie. D’autres réglages techniques sont mémorisés automatiquement par Teamworks dans la configuration utilisateur.

## Où le trouver ?

Menu principal **Paramétrage**. Certaines commandes ne prennent leur sens qu’une fois un dossier ouvert.

## Groupes réellement exposés

### Général et accès

- **Enregistrement** ;
- gestion des **Gadgets** de la page d’accueil ;
- **Accès réseau** ;
- **Adresses d’expédition d’Emails** ;
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

Les groupes/barèmes CCNS et CEE modernes possèdent aussi leurs propres écrans d’édition accessibles depuis les dialogues de contrat lorsque le moteur les expose.

### Recrutement

- protection des entretiens ;
- fonctions ;
- affectations ;
- diffuseurs ;
- offres d’emploi.

### Calendrier

- vacances ;
- jours fériés.

<a id="parametres-effets"></a>
## Paramètres et effets

| Paramètre | Effet vérifié | Portée | Redémarrage nécessaire |
|---|---|---|---|
| Questionnaire | définit les questions proposées dans la fiche | dossier | non observé dans le code audité |
| Types de qualifications | alimente les qualifications des personnes/candidats | dossier | non observé |
| Types de pièces | alimente les pièces à fournir/recevoir | dossier | non observé |
| Catégories de présences | alimente la saisie des présences | dossier | non observé |
| Types/modèles/champs de contrats | alimente l’assistant et les documents de contrat | dossier | non observé |
| Fonctions/affectations/offres | alimente le recrutement | dossier | non observé |
| Vacances / jours fériés | alimente le calendrier et certaines conditions de sauvegarde | dossier | non observé |
| Accès réseau | configure l’accès au mode réseau/MySQL | connexion/dossier | dépend du changement effectué ; **À confirmer en recette fonctionnelle** |
| Adresse d’expédition Email | fournit les paramètres utilisés par les envois | dossier/configuration | non observé |
| Protection par mot de passe | protège l’ouverture du dossier | dossier | non observé |

Le code audité ne fournit pas un groupe générique « Utilisateurs » indépendant ; ne confondez pas **Accès réseau** avec une gestion complète de comptes applicatifs.

## Paramètres mémorisés automatiquement

Teamworks conserve notamment : dernier dossier et dossiers récents, taille de fenêtre, interface MySQL choisie, présentation des listes et plusieurs choix du publipostage (éditeur, modèle, options de sortie).

<a id="champs-personnalises"></a>
## Champs personnalisés

Deux mécanismes sont importants pour les documents :

- les **champs personnalisés de publipostage** enregistrés dans le dossier et gérés depuis l’étape de vérification de l’assistant ;
- les **champs de contrats**, configurés via **Paramétrage > Contrats > Les champs de contrats**, dont le mot-clé est stocké dans le dossier.

Le wiki ne peut pas lister leurs noms, car ils dépendent de votre base. Pour retrouver le mot-clé exact, ouvrez la grille **Vérification des données du document** du publipostage ou le paramétrage du champ concerné. Ne devinez jamais une balise. Voir [[Mots-clés de publipostage]].

## Réseau / MySQL

Les paramètres réseau modifient la façon dont Teamworks ouvre le dossier. Faites une sauvegarde avant toute conversion ou modification sensible. Voir [[Données, sauvegardes et MySQL]].

## Points d’attention

- Modifier un référentiel peut changer les choix proposés dans des fiches existantes.
- Les classifications et valeurs de point sont conservées pour compatibilité historique ; elles ne remplacent pas les contrôles CCNS/CEE modernes.
- Les effets visuels immédiats et besoins éventuels de réouverture d’un écran restent **À confirmer en recette fonctionnelle** lorsque le code ne l’impose pas explicitement.

## Liens associés

[[Individus et fiches]] · [[Contrats, CCNS et CEE]] · [[Recrutement]] · [[Présences et planning]] · [[Mots-clés de publipostage]]
