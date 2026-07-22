# Roadmap Teamworks-CCNS — TW-052 à TW-060

## Statut du document

Cette roadmap est une **reconstruction validée à partir de l’état réel du dépôt après TW-051**. Les formulations originales de TW-052 à TW-060 n’ayant pas été conservées, ce document devient la référence officielle pour la suite.

État de départ vérifié :

- TW-048 : contrats Teamworks raccordés au contrôle salarial ;
- TW-049 : audit CCNS raccordé au contrôleur salarial ;
- TW-050 : détail du contrôle salarial affiché dans l’audit ;
- TW-051 : filtres et tris salariaux ajoutés dans l’audit.

## Principes de gouvernance

- Une TW ne démarre qu’après fusion de la précédente, sauf décision explicite.
- Chaque TW doit produire une PR dédiée vers `master`.
- Les calculs métier existants ne doivent pas être dupliqués dans l’interface.
- Les valeurs monétaires restent des `Decimal` jusqu’aux frontières d’affichage ou d’export.
- Les filtres, tris, exports et vues utilisent les résultats déjà calculés lorsque cela est possible.
- Toute modification de cette roadmap doit être versionnée dans GitHub.

---

## TW-052 — Ajouter la fiche de détail d’un contrôle salarial

**Statut : Réalisée.**

**PR : #99.**

### Objectif

Permettre d’ouvrir depuis l’audit CCNS une fiche détaillée pour une ligne de contrat, sans recalculer le contrôle salarial.

### Périmètre

- afficher salarié, contrat, classification, rémunération, minimum applicable, source, écart et statut ;
- afficher les motifs de non-évaluation et les anomalies ;
- conserver les valeurs brutes et les libellés déjà exposés ;
- rester compatible avec wxPython et les couches applicatives existantes.

### Critères de sortie

- ouverture depuis une ligne d’audit ;
- fonctionnement pour conforme, non conforme et non évaluable ;
- aucun second calcul salarial ;
- tests ciblés et suite complète verte.

---

## TW-053 — Ajouter la synthèse salariale d’un salarié

**Statut : Réalisée.**

**PR : #100.**

### Objectif

Regrouper les contrôles salariaux de tous les contrats d’un salarié dans une synthèse unique.

### Périmètre

- sélection par identifiant salarié ;
- liste ordonnée des contrats contrôlés ;
- compteurs par statut ;
- total des écarts salariaux ;
- accès au détail de chaque contrat.

### Critères de sortie

- synthèse exacte à partir des résultats du contrôleur ;
- absence de doublons ;
- conservation de l’ordre déterministe ;
- export possible via les mécanismes existants ou une adaptation limitée.

---

## TW-054 — Ajouter les indicateurs salariaux au tableau de bord CCNS

**Statut : Réalisée.**

**PR : #101.**

### Objectif

Afficher sur le tableau de bord CCNS les principaux indicateurs du contrôle salarial.

### Périmètre

- nombre de contrats contrôlés ;
- conformes, non conformes et non évaluables ;
- montant total des écarts ;
- date de référence du contrôle ;
- accès direct à l’audit filtré.

### Critères de sortie

- indicateurs issus du contrôleur applicatif ;
- aucune lecture ou logique métier dupliquée dans le tableau de bord ;
- comportement défini pour un lot vide ou incomplet.

---

## TW-055 — Ajouter l’historique des contrôles salariaux

**Statut : Réalisée.**

**PR : #102.**

### Objectif

Conserver une trace datée des contrôles exécutés afin de comparer les résultats dans le temps.

### Périmètre

- définir un modèle de snapshot immuable ;
- conserver date de référence, date d’exécution, compteurs et écarts ;
- identifier les contrats et salariés concernés ;
- ne pas persister les libellés d’interface comme source de vérité.

### Critères de sortie

- stockage déterministe et versionné ;
- lecture de l’historique sans recalcul ;
- compatibilité avec les contrôles existants ;
- migration ou création de table documentée.

---

## TW-056 — Ajouter la comparaison entre deux contrôles salariaux

**Statut : En cours.**

**PR : à ouvrir.**

### Objectif

Comparer deux snapshots afin d’identifier les améliorations, dégradations et changements de statut.

### Périmètre

- contrats devenus conformes ;
- contrats devenus non conformes ;
- nouveaux contrats et contrats absents ;
- évolution des écarts ;
- synthèse globale et détail par contrat.

### Critères de sortie

- comparaison pure et déterministe ;
- aucune réévaluation métier ;
- résultat immuable, testable et indépendant de l’interface.

### Suivi

- Modèles, service pur, cas d’usage, présentation et interface d’historique ajoutés.
- Documentation : `docs/42-comparaison-controles-salariaux.md`.

---

## TW-057 — Ajouter le suivi des anomalies salariales

### Objectif

Permettre de suivre le traitement d’une anomalie salariale sans modifier le résultat métier d’origine.

### Périmètre

- statuts de suivi : à traiter, en cours, corrigée, classée ;
- commentaire interne facultatif ;
- date et auteur de la dernière action ;
- lien stable avec le contrat, le salarié et le snapshot concerné.

### Critères de sortie

- séparation stricte entre anomalie métier et suivi opérationnel ;
- historique minimal des changements ;
- droits d’accès préparés pour les futures interfaces.

---

## TW-058 — Ajouter les alertes de contrôle salarial

### Objectif

Détecter les situations qui nécessitent l’attention de la direction ou de la comptabilité.

### Périmètre

- nouveau contrat non conforme ;
- augmentation d’un écart ;
- contrat toujours non évaluable ;
- anomalie non traitée depuis un délai configurable ;
- seuils et règles déterministes.

### Critères de sortie

- moteur d’alertes indépendant de l’interface ;
- aucune notification externe imposée à ce stade ;
- alertes consultables et testées sans dépendance réseau.

---

## TW-059 — Ajouter l’export consolidé du suivi salarial

### Objectif

Exporter une vue consolidée combinant résultat du contrôle, historique et suivi des anomalies.

### Périmètre

- export CSV et JSON ;
- filtres par période, salarié, statut métier et statut de suivi ;
- conservation exacte des montants ;
- noms de fichiers déterministes ;
- aucun accès direct aux interfaces graphiques.

### Critères de sortie

- réutilisation des façades et contrôleurs d’export existants ;
- absence de duplication de la sérialisation ;
- export testable sans écriture disque automatique.

---

## TW-060 — Stabiliser le module de contrôle salarial pour une première utilisation réelle

### Objectif

Finaliser le périmètre contrôle salarial sous forme d’un jalon utilisable par l’association.

### Périmètre

- audit de cohérence des TW-026 à TW-059 ;
- tests de non-régression et scénarios de bout en bout ;
- vérification des imports et dépendances circulaires ;
- documentation d’utilisation ;
- procédure de sauvegarde et restauration des données ajoutées ;
- liste explicite des limites restant hors périmètre.

### Critères de sortie

- suite complète verte ;
- scénario réel documenté : contrats Teamworks → contrôle → audit → détail → historique → suivi → export ;
- aucune régression connue bloquante ;
- version ou tag de jalon prêt à tester sur une copie de la base PMSL.

---

## Ordre de réalisation

1. TW-052 — détail d’un contrôle ;
2. TW-053 — synthèse salarié ;
3. TW-054 — tableau de bord ;
4. TW-055 — historique ;
5. TW-056 — comparaison ;
6. TW-057 — suivi des anomalies ;
7. TW-058 — alertes ;
8. TW-059 — export consolidé ;
9. TW-060 — stabilisation du jalon.

## Suivi

| TW | Intitulé | Statut | PR |
|---|---|---|---|
| TW-052 | Fiche de détail d’un contrôle salarial | Réalisée | #99 |
| TW-053 | Synthèse salariale d’un salarié | Réalisée | #100 |
| TW-054 | Indicateurs salariaux du tableau de bord | Réalisée | #101 |
| TW-055 | Historique des contrôles salariaux | Réalisée | #102 |
| TW-056 | Comparaison de contrôles salariaux | Planifiée | — |
| TW-057 | Suivi des anomalies salariales | Planifiée | — |
| TW-058 | Alertes de contrôle salarial | Planifiée | — |
| TW-059 | Export consolidé du suivi salarial | Planifiée | — |
| TW-060 | Stabilisation du module salarial | Planifiée | — |
