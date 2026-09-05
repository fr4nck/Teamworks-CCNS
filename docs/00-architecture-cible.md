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
- écrans de contrôle.

## Transition Vanilla vers Qt

**Teamworks Vanilla reste la référence métier pendant la migration vers Qt.**

- Vanilla est stabilisé : il n'a plus vocation à recevoir de grandes refontes d'interface.
- Les nouveaux développements UI structurants ont vocation à être réalisés en Qt.
- La migration est progressive, écran par écran et domaine par domaine.
- Qt ne doit pas embarquer directement du SQL ou des règles métier qui peuvent être séparées de l'interface.
- Le comportement wxPython historique n'est pas automatiquement normatif : un bug identifié doit être corrigé ou explicitement arbitré avant d'être reproduit en Qt.

Le gel de Vanilla **n'interdit pas les corrections**. Restent autorisés :
- bugs fonctionnels ;
- bugs graphiques, de layout, de thème, de zoom ou de rendu ;
- régressions ;
- corrections de règles métier erronées ;
- conformité CCNS, réglementaire ou sociale ;
- sécurité ;
- compatibilité avec les environnements de production ;
- adaptations limitées nécessaires à une migration Qt propre.

Principe : **on corrige ce qui dysfonctionne dans Vanilla, mais on évite d'y investir dans une nouvelle refonte UI destinée à être remplacée par Qt.**

## Règle simple
**WordPress transmet, Teamworks décide.**
