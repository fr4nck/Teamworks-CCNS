# Architecture cible du fork Teamworks orienté CCNS

## Décision retenue
- **Teamworks forké orienté CCNS** = cœur métier principal
- **Passerelle WordPress** = couche de liaison avec l'écosystème existant
- **Noethys / Connecthys / DocuSign / Mailjet** = outils connectés autour

## Rôle du cœur Teamworks
Le cœur Teamworks doit porter :
- gestion des personnes ;
- profils juridiques ;
- contrats ;
- régimes d'emploi ;
- classifications ;
- grilles salariales ;
- règles de calcul ;
- anomalies ;
- habilitations ;
- historique sensible ;
- écrans de contrôle ;
- données RH structurées susceptibles d'alimenter les exports et, à terme seulement si cette décision est prise, une production de paie.

## Préparation future de la paie

La priorité reste la fiabilité du périmètre RH existant. Teamworks-CCNS ne lance pas actuellement de moteur de paie, de bulletin natif ni de génération DSN.

En revanche, les nouvelles fonctions RH doivent éviter d'écraser ou de perdre les informations qui pourraient ultérieurement être nécessaires pour préparer, expliquer ou contrôler une rémunération : historique contractuel, classification, rémunération, temps, absences, protection sociale, organismes, variables, sources et justificatifs.

Cette orientation est détaillée dans `docs/67-fondations-rh-paie-ready.md`. Elle impose une discipline de modélisation et de traçabilité, sans transformer le périmètre actuel en projet de logiciel de paie.

## Règle simple
**WordPress transmet, Teamworks décide.**