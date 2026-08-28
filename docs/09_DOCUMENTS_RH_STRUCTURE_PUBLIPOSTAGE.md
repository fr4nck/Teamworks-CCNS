# Documents RH, profil Structure et publipostage

**Statut : décision fonctionnelle à conserver, implémentation progressive**  
**Date : 28 août 2026**

Ce document complète `08_OCR_IMPORT_DOCUMENTAIRE_RH.md`. Il ne transforme pas Teamworks en GED universelle : il fixe la propriété des documents RH, la source des données de structure utilisées dans les modèles et le comportement attendu du publipostage.

## 1. Propriété des documents RH

Teamworks-CCNS reste la source de vérité pour les documents relevant du dossier RH :

- contrats et avenants ;
- diplômes et habilitations ;
- cartes professionnelles ;
- pièces administratives salariées ;
- documents liés aux absences, entrées et départs ;
- autres documents strictement rattachés au parcours RH.

Une future façade web ou un portail salarié pourra **exposer** certains documents ou métadonnées autorisés, mais ne doit pas déplacer silencieusement leur source de vérité hors de Teamworks.

Le portail est donc un canal d'accès ou d'échange ; Teamworks conserve la responsabilité métier du dossier RH.

## 2. Moteur documentaire RH générique et multi-structure

Le moteur de documents doit pouvoir fonctionner pour plusieurs structures utilisatrices sans données PMSL codées en dur.

Les modèles doivent distinguer au minimum :

- les données du salarié ;
- les données du contrat ou objet RH concerné ;
- les données de la structure employeur ;
- les données calculées ou réglementaires ;
- les champs propres au document ou au modèle.

La structure employeur est une donnée métier de Teamworks et doit être accessible de façon canonique, indépendamment du format historique de stockage.

## 3. Profil canonique `Structure`

Teamworks doit converger vers un profil canonique de structure servant de source aux documents, courriers et modèles de publipostage.

Premiers champs à couvrir :

- dénomination / nom de la structure ;
- SIRET ;
- code APE / NAF ;
- adresse ;
- code postal ;
- ville ;
- téléphone ;
- email ;
- site web ;
- logo ;
- RNA lorsque pertinent ;
- numéro ou référence d'agrément lorsque pertinent.

Cette liste est extensible sans modifier le principe : les documents demandent des **clés sémantiques de structure**, pas un accès direct à une table ou à une clé historique.

## 4. Compatibilité avec les données historiques

Des informations de structure existent déjà dans les installations historiques, notamment dans `due_valeurs` ou d'autres mécanismes hérités.

La modernisation ne doit ni perdre ni dupliquer ces données à l'aveugle.

Ordre cible :

1. inventorier les clés historiques réellement présentes ;
2. définir leur correspondance avec le profil canonique `Structure` ;
3. lire l'existant via un adaptateur de compatibilité ;
4. prévoir une migration explicite uniquement lorsque le nouveau stockage est stabilisé ;
5. conserver un retour compatible pendant la période de transition ;
6. ne jamais imposer une migration de ces données par l'installateur.

La présence historique de `due_valeurs` est donc un matériau de migration, pas le contrat applicatif futur.

## 5. Contrat de publipostage

Le moteur de publipostage doit être prévisible et permettre de détecter les erreurs de modèle.

### Clé connue mais valeur absente

Si une clé appartient au catalogue connu mais que la structure ou le salarié n'a pas de valeur renseignée, le résultat doit être **vide**.

Exemple conceptuel : une structure sans site web renseigné ne doit pas produire un jeton brut dans le document final.

### Clé réellement inconnue

Si le modèle contient une clé que Teamworks ne connaît pas, le jeton doit rester **visible** dans le résultat ou être signalé explicitement lors de la prévisualisation.

Objectif : ne pas masquer une faute de frappe ou une variable de modèle non supportée.

Ainsi :

`clé connue + donnée absente → vide`

`clé inconnue → visible / signalée`

## 6. Prévisualisation et validation des modèles

Avant génération définitive d'un document RH, Teamworks doit pouvoir signaler :

- les clés inconnues ;
- les champs connus mais non renseignés lorsque leur absence est importante ;
- l'identité de la structure utilisée ;
- l'identité du salarié / contrat concerné ;
- le modèle utilisé.

Une prévisualisation ne doit pas modifier les données métier.

## 7. Lien avec l'OCR documentaire

Le moteur OCR décrit dans `08_OCR_IMPORT_DOCUMENTAIRE_RH.md` lit les documents entrants et propose des données à valider.

Le moteur de documents/publipostage fait le chemin inverse : il exploite les données validées de Teamworks pour produire un document.

Les deux partagent des concepts communs — document, type, provenance, salarié, structure — mais restent des services distincts :

`document entrant → OCR/extraction → validation → données RH`

`données RH + structure + modèle → prévisualisation → document sortant`

## 8. Portail salarié et GED transverse

Une future façade ou un portail salarié pourra permettre, selon les droits :

- consultation de documents RH publiés ;
- dépôt de pièces par le salarié ;
- notification de nouvelles pièces ;
- récupération de documents générés par Teamworks.

Le flux devra préserver la propriété : un document RH validé et classé appartient au dossier Teamworks même s'il transite par une façade web ou un service documentaire transversal.

Un service GED transverse peut fournir stockage technique, indexation, prévisualisation ou transport, mais il ne devient pas automatiquement propriétaire du sens métier du document.

## 9. Garde-fous

- aucun champ PMSL codé en dur dans le moteur générique ;
- aucune écriture silencieuse depuis OCR ou portail ;
- aucune migration documentaire déclenchée par l'installateur ;
- permissions RH et règles de confidentialité conservées ;
- les anciens modèles doivent rester interprétables autant que raisonnablement possible ;
- les nouvelles clés de publipostage doivent être documentées et testables.

## 10. Prochaine étape technique lorsqu'elle sera priorisée

1. inventorier les clés `due_valeurs` réellement utilisées pour la structure ;
2. inventorier les variables actuellement utilisées par les modèles de documents ;
3. définir le catalogue de clés canoniques `Structure` ;
4. créer un adaptateur lecture historique → profil canonique ;
5. ajouter une validation de modèle distinguant clé connue vide et clé inconnue ;
6. seulement ensuite faire évoluer le stockage ou l'interface de gestion de la structure.
