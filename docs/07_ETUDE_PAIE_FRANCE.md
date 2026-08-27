# Étude des solutions de paie française — articulation avec Teamworks-CCNS

**Statut : document vivant**  
**Créé : 27 août 2026**

> Ce document n'est pas une feuille de route. Il conserve les résultats de recherche sur les moteurs de paie français susceptibles de recevoir des données préparées par Teamworks-CCNS.

## 1. Principe d'architecture

Teamworks-CCNS n'a pas vocation à devenir un logiciel de paie complet.

Sa valeur propre est située en amont :
- dossier salarié ;
- contrats ;
- classification CCNS ;
- groupe / minima ;
- temps contractuel ;
- CDD / CDI / CEE ;
- absences et éléments RH ;
- contrôles et anomalies ;
- préparation des éléments nécessaires à la paie.

La paie française implique en plus un moteur légal continuellement maintenu : cotisations, plafonds, exonérations, prélèvement à la source, bulletins, DSN mensuelles, signalements, organismes complémentaires et mises à jour conventionnelles.

Le scénario privilégié à étudier est donc :

**Teamworks-CCNS → données RH et variables préparées → moteur de paie spécialisé → bulletin / DSN / écritures comptables.**

## 2. OpenConcerto

OpenConcerto est une solution française de gestion d'entreprise sous licence libre, comportant un véritable module de paie.

Fonctions constatées :
- fiches de paie ;
- rubriques de paie configurables ;
- profils de paie ;
- variables et formules de calcul ;
- journaux / livre de paie ;
- congés maladie ;
- prélèvement à la source ;
- écritures comptables ;
- génération DSN via module dédié ;
- plusieurs contrats pour un salarié dans la version 1.7.6 ;
- gestion de la réduction générale dégressive unique (RDGU) dans la version 1.7.6.

La version 1.7.5 a intégré une mise à jour du système de paie pour 2025. La version 1.7.6 est la version diffusée au moment de l'étude, et une version 1.8 est en préparation en 2026.

### DSN

Le module DSN est maintenu par l'éditeur et facturé séparément afin de financer le suivi de la norme. Le tarif public annoncé est de 3 jetons, soit 72 € HT pour le module et ses mises à jour pendant un an.

### Convention collective du sport

Aucune prise en charge native et maintenue de la CCNS n'a été identifiée. OpenConcerto permet de composer des profils et rubriques correspondant à une convention collective, mais cela implique de paramétrer et maintenir soi-même les spécificités conventionnelles.

### Appréciation

**Atouts :** libre, français, paie réelle, DSN, coût faible, installable localement, données accessibles.

**Limites :** la maintenance de la CCNS resterait largement à notre charge ; la publication du code source a historiquement connu des décalages avec les versions binaires ; la paie exige un paramétrage expert.

**Verdict : candidat libre le plus concret, mais pas une solution CCNS prête à l'emploi.**

## 3. OpenPaie de Sudokeys sur Odoo

Attention à ne pas confondre avec OpenPaye (section suivante).

Sudokeys présente OpenPaie comme une solution de paie open source intégrée à Odoo et maintenue depuis près de dix ans.

Fonctions annoncées :
- paie française ;
- DSN et télédéclarations ;
- fortes volumétries ;
- webservices ;
- veille légale ;
- suivi des conventions collectives ;
- intégration aux fonctions RH d'Odoo.

Des cas clients publics indiquent une production de bulletins et télédéclarations via OpenPaie/Odoo.

### Point de vigilance sur le caractère libre

Sudokeys qualifie OpenPaie d'open source, mais aucun dépôt public OpenPaie ni paquet publiquement téléchargeable n'a été identifié lors de cette étude. Les modules publics Sudokeys disponibles sur l'Odoo Apps Store ne comprennent pas OpenPaie.

Il faut donc distinguer :
- la philosophie et le socle Odoo open source ;
- le produit OpenPaie dont les conditions exactes d'accès au code, de licence et de redistribution restent à confirmer auprès de Sudokeys.

**Verdict : solution professionnelle techniquement crédible, mais caractère réellement exploitable comme logiciel libre à confirmer.**

## 4. Odoo Community + OCA Payroll

L'Odoo Community Association maintient un moteur de paie générique pour Odoo 18 sous licences libres.

Il fournit notamment :
- structures de salaire ;
- règles de salaire ;
- bulletins ;
- lots de bulletins ;
- contrats ;
- intégration comptable ;
- avantages contractuels ;
- interaction avec les jours fériés / absences.

Cependant il s'agit d'un **moteur générique**, pas d'une localisation de paie française complète.

Aucun ensemble public maintenu fournissant à la fois règles françaises, DSN et CCNS n'a été identifié dans l'OCA lors de l'étude.

La documentation officielle récente d'Odoo cite certains modules de paie/comptabilité française, mais la France n'apparaît pas dans la liste officielle des pays disposant d'une localisation complète de paie. Le moteur de paie officiel moderne d'Odoo a par ailleurs été déplacé vers l'édition Enterprise à partir d'Odoo 13 ; l'OCA fournit aujourd'hui un moteur communautaire libre de remplacement.

**Verdict : très bon socle technique pour développer une paie française, mais cela reviendrait à construire et maintenir nous-mêmes une partie très importante du moteur légal. Non recommandé pour PMSL.**

## 5. XOpenDSN

Dépôt : `xopendsn/DSN`.

Projet open source PHP visant à générer une DSN française et un bulletin de paie PDF.

Limites déclarées par son auteur :
- un seul salarié ;
- un seul établissement ;
- projet à compléter et redévelopper.

L'historique public GitHub identifié ne contient que trois commits en mai 2023 et aucune activité ultérieure au moment de l'étude.

**Verdict : prototype / référence technique, pas une solution de production.**

## 6. OpenAccountants — règles françaises

Le projet OpenAccountants contient en 2026 une documentation structurée de règles de paie française (URSSAF, PAS, AGIRC-ARRCO, DSN, etc.).

Cette partie est explicitement marquée comme nécessitant encore une validation par un expert-comptable français.

Il ne s'agit pas, à ce stade, d'un logiciel français de paie prêt pour la production.

**Verdict : source de connaissances potentielle, pas moteur de paie exploitable.**

## 7. OpenPaye — solution SaaS propriétaire mais particulièrement pertinente

OpenPaye (avec un `y`) n'est pas une solution libre : c'est un logiciel de paie français en mode SaaS.

Il est néanmoins très pertinent comme cible éventuelle d'intégration avec Teamworks-CCNS.

Fonctions constatées :
- bulletins de paie ;
- calcul des cotisations ;
- prélèvement à la source ;
- DSN mensuelles et signalements ;
- contrats et salariés ;
- soldes de tout compte ;
- documents de sortie ;
- virements SEPA ;
- exports comptables ;
- API selon l'offre ;
- mises à jour légales et conventionnelles automatiques.

### Point déterminant pour PMSL : CCNS prise en charge

La liste publique des conventions maintenues par OpenPaye contient explicitement :

**Sport — IDCC 2511.**

OpenPaye indique maintenir pour les conventions notamment :
- classifications ;
- minima conventionnels ;
- apprentissage / alternance ;
- prévoyance ;
- majorations ;
- primes ;
- maintien de salaire ;
- congés conventionnels.

Des mises à jour publiques consacrées à la convention du sport sont également visibles dans son historique de veille conventionnelle.

### Tarification publique au 27 août 2026

- offre Basique : 0 € jusqu'à 3 salariés et 1 SIRET ;
- offre Confort : 49 € HT / mois + 5 € / mois par salarié à partir du quatrième ;
- l'offre Confort inclut notamment multi-convention, mises à jour, SEPA, portail, multi-utilisateurs et API selon la grille publique.

**Verdict : pas libre, mais candidat opérationnel très sérieux pour externaliser le moteur de paie tout en gardant Teamworks-CCNS comme cœur RH spécialisé. À étudier en priorité si une intégration de paie devient souhaitable.**

## 8. QuickPaie / QuickDSN

Des solutions récentes proposent gratuitement ou à faible coût bulletins et DSN, avec calcul automatique des cotisations.

Elles ne sont pas identifiées comme logiciels libres lors de cette étude et disposent d'un historique plus court que les solutions précédentes.

**Verdict : alternatives commerciales à surveiller, mais pas candidates à une intégration structurante sans audit supplémentaire.**

## 9. Classement synthétique

| Solution | Libre / source accessible | Paie française | DSN | CCNS 2511 maintenue | Maturité pour production PMSL | Intérêt |
|---|---|---|---|---|---|---|
| OpenConcerto | Oui pour le cœur ; publication des sources à auditer version par version | Oui | Oui, module maintenu payant | Non identifiée | Bonne avec expertise paie | **Meilleur candidat libre** |
| OpenPaie / Sudokeys | Présenté open source, mais code public non identifié | Oui | Oui | Suivi de conventions annoncé, détail à confirmer | Forte | **À investiguer auprès de l'éditeur** |
| Odoo Community + OCA Payroll | Oui | Moteur générique | Non identifié pour France | Non | Faible sans gros développement | Bon laboratoire, mauvais projet PMSL |
| XOpenDSN | Oui | Prototype | Prototype | Non | Très faible | Référence technique seulement |
| OpenAccountants | Oui / connaissances | Non, documentation/règles | Documentation | Non | Nulle en production | Source documentaire |
| OpenPaye SaaS | Non | Oui | Oui | **Oui, IDCC 2511** | Forte | **Meilleur candidat pratique repéré** |
| QuickPaie / QuickDSN | Non identifié comme libre | Oui annoncé | Oui annoncé | À vérifier | À auditer | Secondaire |

## 10. Conclusion architecturale provisoire

L'étude ne justifie pas de transformer Teamworks-CCNS en logiciel de paie.

Au contraire, elle renforce le découpage suivant :

1. **Teamworks-CCNS** conserve la vérité RH et conventionnelle propre à PMSL : salarié, contrat, CCNS, temps contractuel, absences, compétences, contrôles.
2. Il prépare les **éléments variables et structurants de paie**.
3. Un moteur de paie français spécialisé reçoit ces données et porte la responsabilité de calcul : cotisations, PAS, bulletin, DSN, signalements et mises à jour légales.
4. L'intégration doit être réversible : exports documentés et possibilité de changer de moteur de paie.

Deux pistes méritent une étude approfondie ultérieure :
- **OpenConcerto**, si l'objectif prioritaire est la maîtrise locale et le logiciel libre ;
- **OpenPaye**, si l'objectif prioritaire est la fiabilité opérationnelle, la CCNS 2511 maintenue et l'automatisation par API.
