# Architecture cible de Teamworks-CCNS

## Portée de ce document

Ce document décrit uniquement les décisions propres à **Teamworks-CCNS**.

Les décisions transverses entre applications, Portail, hébergement et infrastructure relèvent de **`fr4nck/PMSL-Arch`** et de ses ADR acceptées. Elles ne doivent pas être redéfinies ici.

## Décision retenue

- **Teamworks-CCNS** = cœur métier RH principal ;
- **Qt / PySide6** = interface desktop cible ;
- trois branches permanentes sont maintenues : **`master`**, **`wx/master`** et **`qt/master`**.

## Rails de développement

### `wx/master`

`wx/master` est le rail wxPython / production et la référence métier historique pendant la transition.

Il reçoit :
- corrections métier communes ;
- conformité CCNS, réglementaire et sociale ;
- sécurité ;
- compatibilité avec les environnements de production ;
- corrections fonctionnelles ;
- corrections UI wxPython nécessaires à la stabilité, au rendu, au layout, au thème ou au zoom ;
- adaptations limitées nécessaires à une migration Qt propre.

Il n'a plus vocation à recevoir de grandes refontes d'interface destinées à être remplacées par Qt.

### `qt/master`

`qt/master` est le rail principal de migration Qt.

Il reçoit :
- nouveaux développements UI structurants ;
- migration progressive des écrans et domaines ;
- composants Qt et leurs tests spécifiques ;
- synchronisations contrôlées des changements métier communs qualifiés sur `master`.

Le rail Qt ne doit pas dupliquer du SQL ou des règles métier qui peuvent être partagés avec le cœur commun.

### `master`

`master` porte les domaines, services, infrastructures, outils, documentation et CI transversaux.

### Synchronisation

Les changements communs sont intégrés et qualifiés sur `master`, puis portés explicitement vers les rails concernés. Un correctif découvert sur wx ou Qt peut être extrait vers le socle partagé.

Les transferts restent ciblés et qualifiés : aucun merge massif entre rails, aucune synchronisation automatique.

Les seules branches de travail autorisées sont `master`, `wx/master` et `qt/master`. Ne pas créer de branche temporaire. Les anciennes branches sont supprimées après conservation de leur contenu utile ou décision explicite d'abandon.

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

## Transition wxPython vers Qt

**Le rail wx reste la référence métier historique pendant la migration vers Qt.**

- wxPython est stabilisé : il n'a plus vocation à recevoir de grandes refontes d'interface.
- Les nouveaux développements UI structurants ont vocation à être réalisés en Qt.
- La migration est progressive, écran par écran et domaine par domaine.
- Qt ne doit pas embarquer directement du SQL ou des règles métier qui peuvent être séparées de l'interface.
- Le comportement wxPython historique n'est pas automatiquement normatif : un bug identifié doit être corrigé ou explicitement arbitré avant d'être reproduit en Qt.

Le gel des refontes wxPython **n'interdit pas les corrections**. Restent autorisés :
- bugs fonctionnels ;
- bugs graphiques, de layout, de thème, de zoom ou de rendu ;
- régressions ;
- corrections de règles métier erronées ;
- conformité CCNS, réglementaire ou sociale ;
- sécurité ;
- compatibilité avec les environnements de production ;
- adaptations limitées nécessaires à une migration Qt propre.

Principe : **on corrige ce qui dysfonctionne dans wxPython, mais on évite d'y investir dans une nouvelle refonte UI destinée à être remplacée par Qt.**

## Historique de qualification Qt

La PR **#366** a qualifié le POC Qt initial sur Linux et Windows. Son HEAD qualifié a servi de point de départ au rail durable **`qt/master`**.

Les PR techniques **#377**, **#378** et **#380** ont été convergées par **#381**, puis fermées comme superseded. La PR #366 a ensuite été fermée sans merge vers la branche historique `master` : elle reste une archive de qualification, pas le mécanisme de développement courant du rail Qt.
