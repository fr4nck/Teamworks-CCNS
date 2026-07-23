# Roadmap Teamworks-CCNS

## Vision

Faire de Teamworks un assistant RH spécialisé pour les structures relevant de la CCNS, capable de contrôler automatiquement la conformité réglementaire des contrats, des rémunérations et, progressivement, du temps de travail.

Le projet doit rester prioritairement utile à Pêle-Mêle : chaque jalon important doit produire une fonctionnalité exploitable sur le terrain, même si elle n'est pas encore complète ou généralisable.

---

## Principes directeurs

- Préserver la base Teamworks historique.
- Ne jamais imposer de ressaisie inutile des salariés ou contrats déjà enregistrés.
- Prévoir les migrations de données avant les refontes d'interface.
- Conserver l'historique des contrats et des grilles salariales.
- Séparer le domaine métier des interfaces graphiques ou web.
- Avancer par jalons fonctionnels plutôt que par micro-tâches isolées.
- Accepter des commits plus importants lorsque la contrainte opérationnelle l'exige.
- Maintenir une application utilisable pendant la transition.

---

## Contexte opérationnel 2026

La rentrée 2026 doit être préparée dans un contexte de disponibilité réduite de la direction, avec une charge accrue sur la gestion des accueils de loisirs.

Conséquence directe pour le développement :

- réduire le nombre d'allers-retours ;
- privilégier les livrables directement testables ;
- documenter clairement les choix ;
- sécuriser les données existantes avant toute modification structurelle ;
- viser un MVP exploitable pour Pêle-Mêle avant de chercher une V2 complète.

---

# MVP - Rentrée 2026

## Objectif

Permettre à Pêle-Mêle de contrôler les contrats et rémunérations de la saison 2026-2027 sans repartir de zéro.

## Livrables attendus

- [ ] Audit de la base Teamworks historique.
- [ ] Identification des tables salariés, contrats et données RH existantes.
- [ ] Consultation des salariés existants.
- [ ] Consultation des contrats existants.
- [ ] Reprise automatique des données disponibles.
- [ ] Ajout ou complément des informations CCNS manquantes.
- [ ] Contrôle salarial CCNS.
- [ ] Diagnostic lisible : conforme, non conforme, données manquantes.
- [ ] Historique des grilles salariales.
- [ ] Export CSV ou JSON des contrôles.

## Critère de réussite

La direction doit pouvoir ouvrir Teamworks, retrouver les salariés déjà enregistrés, consulter leurs contrats, compléter les champs CCNS nécessaires et obtenir un diagnostic salarial fiable.

---

# Version 1 - Moteur CCNS stable

## Objectif

Stabiliser le moteur réglementaire CCNS et disposer d'un socle métier propre, testable et indépendant de l'interface.

## Livrables attendus

- [ ] Gestion complète des contrats.
- [ ] Classification CCNS par groupe.
- [ ] Contrôle des minima conventionnels.
- [ ] Grilles salariales historisées et datées.
- [ ] Gestion des temps partiels.
- [ ] Gestion des apprentis.
- [ ] Gestion des alternants.
- [ ] Gestion des CEE.
- [ ] Gestion des stagiaires.
- [ ] Gestion des services civiques.
- [ ] Gestion des salariés mineurs.
- [ ] Présentateurs applicatifs stables.
- [ ] Contrôleurs indépendants de la technologie d'interface.
- [ ] Tests unitaires sur les règles métier principales.

## Critère de réussite

Le moteur doit pouvoir répondre à la question suivante : pour une personne, un contrat, une date de référence et une rémunération donnée, la situation est-elle conforme à la CCNS ?

---

# Version 2 - Outil de gestion quotidien

## Objectif

Transformer le moteur CCNS en outil utilisable régulièrement par la direction, la comptabilité et les profils autorisés.

## Livrables attendus

- [ ] Import Excel ou CSV.
- [ ] Import depuis Noethys ou export Noethys.
- [ ] Tableau de bord global.
- [ ] Recherche multicritères.
- [ ] Filtres par salarié, contrat, groupe, période et statut.
- [ ] Edition contrôlée des contrats.
- [ ] Rapports PDF.
- [ ] Statistiques RH simples.
- [ ] Exports utilisables pour la paie ou la comptabilité.
- [ ] Gestion des droits selon les profils internes.

## Critère de réussite

Teamworks doit devenir un outil de suivi RH régulier et non plus seulement un moteur de vérification ponctuelle.

---

# Version 3 - Assistant RH élargi

## Objectif

Etendre Teamworks au-delà des seuls contrats et salaires pour couvrir les principaux suivis RH et réglementaires de l'association.

## Livrables possibles

- [ ] Suivi du temps de travail.
- [ ] Congés.
- [ ] Absences.
- [ ] Arrêts maladie.
- [ ] Accidents du travail.
- [ ] Formations obligatoires.
- [ ] AFDAS.
- [ ] Médecine du travail.
- [ ] DUERP.
- [ ] Matériel confié.
- [ ] Véhicules.
- [ ] Documents salariés.
- [ ] Signatures électroniques.

---

# Long terme

- Interface web responsive.
- Veille automatique CCNS, SMIC et CEE.
- OCR des documents RH.
- Portail salarié.
- Portail bureau avec droits limités.
- Multi-associations.
- API publique ou semi-publique.
- Séparation propre entre le coeur Teamworks et les extensions conventionnelles.

---

# Mode de développement retenu

Le développement doit rester compatible avec la charge opérationnelle de Pêle-Mêle.

Lorsque la disponibilité est réduite, les commits peuvent regrouper davantage de changements, à condition de rester cohérents et testables. L'objectif n'est pas de produire le plus grand nombre de commits possible, mais de sécuriser des jalons utiles.

Chaque jalon doit idéalement préciser :

- le besoin couvert ;
- les fichiers principaux modifiés ;
- les tests ou vérifications effectués ;
- les limites connues ;
- la suite logique.
