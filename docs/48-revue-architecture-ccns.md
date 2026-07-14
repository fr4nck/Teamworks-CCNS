# Revue critique de l'architecture Teamworks-CCNS

## Objet et périmètre

Cette revue consolide l'état architectural après l'ajout de la couche de lecture, des readers `CcnsDataReader` et `PersonReader`, de l'instrumentation de performance, de la veille réglementaire, du versionnement documentaire des règles et des grilles, des dépôts mémoire et de leur intégration au `RuntimeContainer`.

Elle ne propose pas de refonte générale. Elle classe l'existant selon six angles : cohérent, redondant, prématuré, manquant, à simplifier et à conserver en l'état.

## Cartographie réelle des flux

### Flux cible posé par les documents

```text
wxPython
→ services applicatifs
→ moteur métier CCNS
→ readers / repositories
→ GestionDB
→ base de données
```

Ce flux est partiellement réel. Il existe aujourd'hui deux chemins principaux :

1. **Chemin runtime pur**, utilisé par les tests, la démonstration et les services applicatifs récents :

```text
scripts / tests
→ RuntimeContainer
→ repositories mémoire
→ entités domaine
→ services de contrôle
```

2. **Chemin Teamworks réel**, utilisé par l'audit CCNS et certains écrans historiques :

```text
wxPython / helpers Teamworks
→ helpers CcnsCore
→ fonctions du moteur métier
→ CcnsDataReader ou PersonReader
→ GestionDB
→ tables historiques et tables tw_*
```

Le chemin Teamworks réel contourne encore souvent les services applicatifs génériques : `audit_contracts` transforme directement les records SQL en objets `Contract`, construit la grille, puis appelle les contrôles du domaine. Ce choix reste acceptable pour une passerelle progressive, mais il doit être assumé comme un adaptateur d'intégration et non comme la couche applicative cible.

### Flux audit des contrats

```text
Audit transverse / gadget / synthèse personne
→ teamworks.CcnsCore.audit_contracts_ccns.audit_contracts
→ CcnsDataReader.lire_contrats ou lire_contrats_personne
→ CcnsDataReader.lire_grilles + lire_lignes_grille
→ GestionDB
→ mapping vers Contract, SalaryGrid, SalaryGridLine
→ contrôles domaine : classification, grille, minimum, ancienneté
→ AuditRow / dictionnaires d'interface
```

Points importants :

- le reader isole les requêtes SQL de lecture des contrats et des grilles ;
- le helper d'audit reste responsable d'une partie du mapping métier ;
- la sélection de la grille lit désormais les grilles réelles disponibles, peut exploiter des versions de grille lorsque le reader les expose, et conserve un repli déterministe compatible avec les bases sans version ;
- la date de référence est `date.today()`, ce qui est pratique pour l'audit courant mais insuffisant pour une relecture historique.

### Flux synthèse individuelle

```text
Fiche individuelle / dossiers incomplets
→ build_person_ccns_summary(IDpersonne)
→ adaptateur _PersonScopedCcnsReader
→ audit_contracts(data_reader=adaptateur)
→ CcnsDataReader.lire_contrats_personne
→ résultats triés par gravité et contrat
```

Ce flux est cohérent : la synthèse individuelle réutilise l'audit transverse sans dupliquer les contrôles. Le risque principal est que l'adaptateur `_PersonScopedCcnsReader` reste implicite et local au helper ; il peut rester ainsi tant que le besoin reste limité.

### Flux lecteurs de personnes

```text
Écrans historiques wxPython
→ PersonReader.lire_identites
→ GestionDB
→ PersonIdentityRecord itérable
→ listes historiques qui dépaquettent encore des tuples
```

Ce flux est une bonne migration locale : le `PersonIdentityRecord` conserve une compatibilité de dépaquetage avec les écrans existants tout en rendant la lecture testable sans wxPython.

### Flux runtime et dépôts mémoire

```text
build_runtime_container()
→ repositories mémoire
→ seed classifications, grille 2026, version de grille 2026, règles par défaut
→ services applicatifs de contrôle
→ vues applicatives
```

Ce flux constitue un banc de montage stable pour le domaine et les tests. Il n'est pas encore le runtime principal de Teamworks réel, car il ne lit pas `GestionDB` et ne persiste pas les nouveaux objets métier.

### Flux réglementaire et versionnement

```text
sources réglementaires / fetcher JSON
→ snapshots et changements
→ RuleReference
→ RuleVersion
→ SalaryGridVersion
→ sélecteurs datés
```

Ce flux est volontairement descriptif. Il documente et sélectionne des versions applicables, mais ne pilote pas encore automatiquement les contrôles ni la grille choisie par l'audit réel. Cette séparation est saine pour éviter une activation réglementaire non validée.

## Ce qui est cohérent

- **Séparation progressive du domaine et de l'historique Teamworks** : les entités CCNS et les contrôles sont placés dans `domain`, tandis que les raccords wxPython et Teamworks restent dans `teamworks/CcnsCore` ou dans les écrans historiques.
- **Readers dédiés au-dessus de `GestionDB`** : `CcnsDataReader` et `PersonReader` diminuent les requêtes dispersées et améliorent la testabilité sans imposer une migration complète de la persistance.
- **DTO de lecture explicites** : les records de `domain/repositories/*_data.py` stabilisent les contrats de lecture entre SQL et domaine.
- **Instrumentation de performance locale** : les readers et l'audit mesurent les requêtes, le fetch et des transformations Python sans modifier les règles métier.
- **Versionnement réglementaire non intrusif** : `RuleReference`, `RuleVersion`, `LegalCertainty` et `SalaryGridVersion` documentent la preuve et la période d'applicabilité sans changer les calculs existants.
- **Dépôts mémoire et `RuntimeContainer` utiles aux tests** : ils permettent de vérifier les services et le domaine sans dépendre de wxPython ni d'une base réelle.
- **Réutilisation de l'audit transverse pour la synthèse individuelle** : cela évite une divergence immédiate entre écran individuel, dossiers incomplets et audit global.

## Ce qui est redondant

- **Deux familles de persistance coexistent** : les repositories mémoire servent le runtime applicatif, tandis que les readers servent les données réelles Teamworks. Ce n'est pas une erreur, mais il faut éviter de les présenter comme deux implémentations équivalentes tant que les repositories ne lisent pas `GestionDB`.
- **`RuleVersion` et `SalaryGridVersion` partagent des statuts et niveaux de validation proches** : la duplication est acceptable pour clarifier les concepts, mais elle devra être surveillée si d'autres objets versionnés apparaissent.
- **Mapping contrat répété potentiellement à venir** : aujourd'hui le mapping SQL → `Contract` est concentré dans l'audit ; si d'autres écrans en ont besoin, il faudra extraire un mapper dédié plutôt que copier la logique.
- **Documents nombreux et proches** : architecture cible, cartographie, couche de données, roadmap readers, versionnement des règles et des grilles se complètent, mais les décisions opérationnelles peuvent devenir difficiles à retrouver.

## Ce qui est prématuré

- **Activation automatique des versions réglementaires** : les sélecteurs datés sont prêts, mais le moteur réel ne doit pas encore changer de comportement automatiquement selon la veille ou une version planifiée.
- **Généralisation des repositories comme persistance principale** : les repositories mémoire sont précieux pour le domaine, mais une migration complète hors `GestionDB` serait trop large à ce stade.
- **Refonte globale de la chaîne wxPython → services** : le flux réel passe encore par des helpers historiques. Une bascule complète vers des services applicatifs doit attendre des besoins concrets et des points de branchement mieux identifiés.
- **Multiplication des readers spécialisés** : `PersonReader` et `CcnsDataReader` sont justifiés. Un nouveau reader doit répondre à une requête réellement répétée ou risquée, pas à une volonté de couvrir toute la base.

## Ce qui manque

- **Contrat d'architecture explicite entre adaptateurs Teamworks et services applicatifs** : il manque une règle simple indiquant quand un helper `teamworks/CcnsCore` peut appeler directement le domaine et quand il doit passer par un service.
- **Persistance des versions de grille dans Teamworks réel** : l'audit sait utiliser des versions exposées par le reader et se replie proprement sur les grilles réelles, mais la lecture SQL dédiée aux versions de grille reste à matérialiser lorsque la table correspondante sera stabilisée.
- **Date de référence injectable dans l'audit** : les contrôles historiques et les tests réglementaires gagneraient à recevoir une date explicite au lieu d'utiliser uniquement la date du jour.
- **Mapper isolé pour SQL → domaine** : la transformation de records `CcnsDataReader` vers `Contract`, `SalaryGrid` et `SalaryGridLine` est assez centrale pour mériter une extraction lorsque le deuxième consommateur apparaît.
- **Politique de cycle de vie des readers** : les readers ferment leur connexion, mais les règles d'usage dans les écrans longs, caches éventuels et erreurs partielles doivent être documentées avant optimisation.
- **Lien lisible entre veille réglementaire et action métier** : les snapshots détectent, les versions documentent, mais le processus humain de qualification, validation et PR métier doit rester décrit dans une checklist courte.

## Ce qui doit être simplifié maintenant

- **La documentation de décision** : ajouter une page de synthèse comme celle-ci et la référencer depuis les futures PR évite de disperser les décisions dans plusieurs documents.
- **Le vocabulaire persistance** : réserver le mot `Reader` aux lectures réelles via `GestionDB` et le mot `Repository` aux collections du domaine/runtime, tant que les deux mondes ne sont pas unifiés.
- **Les ambitions de court terme** : limiter les prochaines PR à des raccords mesurables, par exemple injection d'une date de référence ou choix daté de grille, plutôt qu'à une refonte transversale.

## Ce qui peut rester en l'état

- **`CcnsDataReader`** peut rester la façade SQL CCNS principale tant que son périmètre reste contrats, classifications, grilles et lignes de grille.
- **`PersonReader`** peut rester limité aux identités minimales, car son rôle actuel est clair et compatible avec les écrans historiques.
- **`RuntimeContainer` et repositories mémoire** peuvent rester des outils de bootstrap, de tests et de démonstration.
- **`RuleReference`, `RuleVersion`, `LegalCertainty` et `SalaryGridVersion`** peuvent rester descriptifs, sans effet automatique sur les calculs.
- **Les helpers `teamworks/CcnsCore`** peuvent continuer à porter l'intégration progressive avec Teamworks, à condition de ne pas y enfouir de nouvelles règles CCNS.

## Recommandations non intrusives

1. **Conserver l'architecture par couches, mais nommer le chemin réel** : documenter que l'intégration Teamworks actuelle passe par des adaptateurs `teamworks/CcnsCore`, pas encore par une couche applicative complète.
2. **Prioriser la date de référence injectable** dans l'audit avant toute évolution réglementaire active.
3. **Stabiliser ensuite la lecture persistée des versions de grille** : le choix daté et le repli existent côté audit, mais la source SQL des versions doit rester une évolution dédiée et testée.
4. **Extraire un mapper SQL → domaine uniquement au deuxième usage** pour éviter une abstraction prématurée.
5. **Maintenir les readers petits et testés** ; chaque nouvelle lecture doit être motivée par un écran, un contrôle ou une suppression de requête dispersée.
6. **Garder la veille réglementaire sans activation automatique** tant que la validation métier et juridique n'est pas matérialisée dans une PR dédiée.

## Conclusion

L'architecture actuelle est globalement cohérente pour un fork en migration progressive : le domaine CCNS est isolé, les premières lectures réelles sont testables, l'instrumentation reste locale et le versionnement réglementaire est descriptif. Les principales fragilités ne justifient pas une refonte générale ; elles concernent surtout la lisibilité des frontières, la sélection datée des grilles, l'injection d'une date de référence et la maîtrise de la duplication entre readers, repositories et helpers Teamworks.
