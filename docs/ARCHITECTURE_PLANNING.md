# Architecture planning — Teamworks CCNS

Ce document détaille les principes d’architecture du moteur de planning. Il ne constitue pas une roadmap concurrente : `ROADMAP.md` reste l’unique source de vérité pour les priorités, jalons et maturité du projet.

## Principes structurants

### 1. Moteur de planning neutre

Le moteur de planning doit rester indépendant d’un métier ou d’une convention collective particulière.

Il manipule notamment :

- organisations et associations ;
- secteurs / coordinations ;
- sites ;
- groupes, sections, cours et activités ;
- personnes, équipes et responsables ;
- créneaux et séances ;
- horaires, pauses et durées ;
- déplacements, trajets, préparation et kilomètres ;
- absences, indisponibilités, remplacements et affectations ;
- périodes scolaires, vacances, jours fériés, fermetures et exceptions.

Les règles conventionnelles sont interprétées au-dessus de ce moteur et ne doivent pas être codées en dur dans l’interface de planning.

### 2. Multi-organisation et multi-association

Le modèle doit pouvoir fonctionner aussi bien pour une petite association que pour une structure importante.

Hiérarchie générique cible :

`Organisation → Association / entité → Secteur / coordination → Site ou section → Groupe / cours → Créneaux → Séances → Affectations`

Le système ne doit contenir aucun site PMSL codé en dur.

Cas de charge de référence pour l’ALSH :

- environ 14 à 15 accueils de loisirs ;
- environ 3 coordinateurs ;
- environ 15 directeurs ;
- environ 15 adjoints ;
- environ 100 animateurs.

L’interface doit rester utilisable et filtrable à cette échelle.

### 3. Rôles, périmètres et permissions

Les droits ne doivent pas dépendre de profils métier rigides.

Le modèle de sécurité repose sur :

- **rôle** : ensemble de capacités ;
- **périmètre** : organisation, association, secteur, site ou ensemble de sites ;
- **permissions** : lecture, modification, validation, export, administration, etc. ;
- **délégation** : attribution temporaire ou durable d’un périmètre ;
- **cumul de rôles** : une même personne peut avoir plusieurs rôles simultanément.

Exemples de profils possibles sans les figer dans le code :

- président ou membre du bureau en lecture globale ;
- directeur d’association avec administration large ;
- directrice adjointe avec droits délégués ;
- secrétaire administrative / RH avec droits sur salariés, contrats, absences et temps de travail ;
- coordinateur avec plusieurs sites ;
- directeur ALSH limité à son accueil ;
- adjoint ALSH avec délégation sur son site.

Une personne peut par exemple avoir des droits RH sur toute l’association, des droits de modification planning sur deux sites et uniquement de la lecture sur les autres.

### 4. Traitement par lot conservé et enrichi

Le traitement par lot existant constitue une bonne base et doit être conservé.

Il doit être enrichi par trois axes :

1. **contexte / site** ;
2. **profils horaires** ;
3. **portée calendrier**.

Le traitement par lot doit pouvoir s’appliquer à :

- un site ;
- plusieurs sites ;
- une coordination ;
- une association ;
- toute l’organisation ;
- une sélection manuelle de personnes ;
- un groupe d’âge ;
- les mineurs uniquement ;
- un métier ou une activité ;
- une combinaison de filtres.

### 5. Portée calendrier

Une opération par lot doit pouvoir cibler uniquement certaines dates :

- toutes les dates ;
- périodes scolaires uniquement ;
- vacances scolaires uniquement ;
- mercredis scolaires ;
- vacances sélectionnées ;
- jours de la semaine sélectionnés ;
- plage personnalisée ;
- fermetures / exceptions exclues.

Cela permet notamment à un éducateur sportif d’avoir ses séances récurrentes pendant les périodes scolaires puis d’être affecté à l’ALSH pendant les vacances, sans écrasement entre les deux ensembles de dates.

### 6. Profils horaires

Les profils horaires doivent être configurables et réutilisables.

Ils peuvent être définis au niveau :

- organisation ;
- association ;
- secteur ;
- site ;
- contexte métier ou période.

Un niveau inférieur peut surcharger un profil hérité.

Exemple ALSH : plusieurs tranches horaires standards différentes le mercredi et pendant les vacances, avec variantes spécifiques pour les mineurs si nécessaire.

La sélection multiple Ctrl/Maj reste disponible comme accélérateur, mais ne doit pas être le seul moyen de saisir des horaires variables.

### 7. Saisie horaire compacte

La saisie horaire doit disposer d’une grille compacte, éditable directement, permettant au minimum :

- début ;
- fin ;
- pause ;
- durée calculée ;
- correction cellule par cellule ;
- copier/coller ;
- duplication d’un jour ou d’un motif ;
- application d’un profil horaire à une sélection.

### 8. Exports

Les exports doivent pouvoir être générés sans Microsoft Excel installé.

Formats cibles :

- `.xlsx` natif ;
- `.csv` pour échanges et imports ;
- PDF pour affichage et impression lorsque pertinent.

Familles d’exports prévues :

#### RH

Vue individuelle ou filtrée avec dates, horaires, pauses, durées, activité, site et totaux.

#### ALSH

Planning par site et période, destiné aux équipes opérationnelles, avec notamment animateurs, horaires, groupes d’âge, remarques et répartition par accueil.

#### Sport

Planning par éducateur, activité, association / section, lieu et période, avec séances, préparation, trajet, kilomètres et remplacements.

L’export doit autant que possible reprendre directement la vue et les filtres actifs à l’écran.

### 9. Fonctionnement hors ligne et synchronisation

Teamworks doit rester pleinement utilisable hors ligne.

La synchronisation avec PMSL-Équipe est un complément, jamais une dépendance pour utiliser le planning localement.

Le modèle cible de synchronisation Teamworks ↔ PMSL-Équipe est inspiré de Connecthys :

- incrémental ;
- bidirectionnel ;
- prévisualisable avant application ;
- idempotent ;
- journalisé ;
- avec détection explicite des conflits ;
- sans écrasement silencieux d’une donnée plus récente.

PMSL-Équipe peut fournir notamment affectations, horaires, activités, sites, kilomètres et remplacements validés. Teamworks peut fournir notamment personnes, contrats, qualifications, absences et indisponibilités.

### 10. Séparation planning / convention collective

Le même moteur de planning doit pouvoir servir à d’autres domaines que la CCNS : entrepôts, logistique, travail posté, convoyage, aéroportuaire ou autres organisations à horaires variables.

Une convention collective ou un accord ajoute des règles d’interprétation :

- durées maximales ;
- repos ;
- pauses obligatoires ;
- heures supplémentaires ;
- majorations ;
- travail de nuit ;
- temps de trajet ;
- règles propres à certaines populations.

Ces règles doivent rester séparées du stockage et de l’édition du planning.

## Principe de conception

Le moteur peut être générique, mais les écrans doivent rester concrets pour les utilisateurs réels. Une interface ALSH doit parler le langage d’un directeur ou coordinateur ALSH ; une interface sport doit parler le langage d’un coordinateur sportif ou éducateur.

La généralisation ne doit être introduite que lorsqu’elle sert un besoin métier réel identifié.