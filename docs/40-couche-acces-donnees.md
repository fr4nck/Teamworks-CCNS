# Couche d'accès aux données CCNS

## Pourquoi introduire cette couche

`teamworks/GestionDB.py` reste le fournisseur historique de données de Teamworks. Il est très transversal : connexion, exécution SQL, compatibilité SQLite/MySQL et usages par les écrans wxPython. Les audits de performance, de compatibilité, de pérennité et d'architecture l'identifient comme un composant critique à moderniser progressivement, sans réécriture globale.

Cette première brique isole les lectures nécessaires au moteur CCNS afin de réduire le couplage entre le domaine CCNS et les requêtes SQL historiques.

## Rôle

La classe `CcnsDataReader`, située dans `infrastructure/persistence/ccns_data_reader.py`, centralise les lectures Teamworks utilisées par l'audit CCNS :

- `lire_contrats()` ;
- `lire_classifications()` ;
- `lire_grilles()` ;
- `lire_lignes_grille()`.

Elle ouvre une connexion via `GestionDB.DB`, exécute des requêtes SQL explicites, puis convertit les tuples historiques en DTO simples définis dans `domain/repositories/ccns_data.py`.

La couche ne contient volontairement aucune règle métier CCNS, aucun calcul de minimum conventionnel et aucune logique wxPython.

## Ce qui est remplacé progressivement

L'audit `teamworks/CcnsCore/audit_contracts_ccns.py` ne construit plus directement les requêtes SQL de lecture des contrats et des grilles. Il consomme désormais un lecteur injecté ou, par défaut, `CcnsDataReader`.

Le comportement métier reste porté par le moteur existant : contrôles simples, contrôle de minimum depuis grille et contrôle d'ancienneté.

## Persistance RH additive via GestionDB

Le chantier Connexions RH introduit également `TeamworksHrConnectionsRepository` dans `infrastructure/persistence/teamworks_hr_connections_repository.py`.

Cet adaptateur ne remplace pas `GestionDB` : il l'utilise comme fournisseur de connexion afin de conserver le contrat historique local SQLite / réseau MySQL. Son périmètre CRH-16 est volontairement limité aux données nécessaires au raccordement « Protection sociale & organismes » :

- profils non secrets des organismes d'une structure ;
- capacités déclarées, références administratives et liens de portail ;
- suivis salarié mutuelle, prévoyance, retraite complémentaire et SPST ;
- périodes d'effet, régime/option, profil de cotisation, justificatif opaque, provenance et échéances administratives.

Le schéma `tw_hr_*` est **additif et versionné**. Il ne modifie aucune table historique et ne crée aucune clé étrangère vers `personnes`, `contrats` ou les autres tables métier existantes. Cette décision permet de préserver l'historique même lorsqu'un organisme est ensuite retiré de la configuration et limite le risque pendant la qualification 0.9.1b.

Les écritures utilisent des transactions explicites et un contrat de paramètres adapté selon `db.isNetwork` : `?` pour SQLite, `%s` pour MySQL. Les upserts spécifiques à SQLite (`ON CONFLICT`, `INSERT OR IGNORE`) sont volontairement exclus de l'adaptateur de production. Les stores SQLite CRH-09 et CRH-13 restent des adaptateurs de qualification ; ils ne sont pas utilisés comme stockage de production par le panneau wxPython.

## Identité stable de la structure active

CRH-17A ajoute `TeamworksStructureIdentityRepository` et un point de composition applicatif pour la synthèse de protection sociale.

La référence de structure **n'est volontairement pas dérivée** du chemin du fichier local, du nom de la base réseau, de l'hôte ou des paramètres de connexion historiques. Ces informations peuvent varier d'un poste à l'autre et, dans le format réseau historique de Teamworks, certaines peuvent contenir des éléments d'authentification. Le premier accès crée donc un UUID opaque dans `tw_hr_structure_identity`, puis tous les postes utilisant cette même base réemploient cette identité.

`EmployeeProtectionSummaryRuntimeFactory` assemble ensuite :

1. l'identité stable de la base Teamworks active ;
2. `TeamworksHrConnectionsRepository` ;
3. `EmployeeProtectionService` ;
4. `EmployeeProtectionSummaryService`.

La façade résultante ne demande à l'interface que la référence du salarié et la date de consultation. Le futur panneau wxPython n'a ainsi ni à sélectionner un backend, ni à fabriquer un `structure_ref`, ni à manipuler la configuration de connexion.

## Ce qui reste historique

Cette évolution ne remplace pas `GestionDB.py` et ne modifie pas ses API. Les autres écrans et modules continuent d'utiliser les accès historiques.

`CcnsDataReader`, `TeamworksHrConnectionsRepository` et le résolveur d'identité sont donc des façades progressives au-dessus de `GestionDB`, compatibles avec la stratégie de migration par périmètres limités : les lectures et écritures nouvelles sont isolées sans disperser de SQL dans l'interface.

## Mesures et performance

Le chemin audit conserve le même volume de requêtes que l'implémentation précédente pour son besoin courant :

1. lecture des contrats ;
2. lecture de la première grille salariale ;
3. lecture des lignes de cette grille.

La connexion `GestionDB.DB()` est ouverte une seule fois par lecteur et réutilisée pour ces lectures, ce qui évite d'introduire des ouvertures supplémentaires. La nouvelle séparation améliore surtout la testabilité et prépare des mesures plus fines sans changer le comportement utilisateur.

Pour Connexions RH, les listes de profils sont chargées par ensembles (en-têtes, capacités, références, liens) afin d'éviter un schéma N+1. Des index additifs ciblent les recherches par structure, salarié, organisme et échéance.

## Prochaines étapes recommandées

1. Étendre progressivement cette couche aux autres lectures CCNS transverses identifiées par les audits.
2. Ajouter des mesures centralisées de temps SQL et temps Python autour du lecteur, désactivées par défaut.
3. Stabiliser des contrats de données plus complets pour les écrans contrats et les tableaux d'audit.
4. Injecter la façade CRH-17A dans la fiche salarié par un raccordement lazy et en lecture seule, sans déplacer le choix du backend dans wxPython.
5. Étendre ensuite la persistance de production aux dossiers `HrCase` et au journal d'audit seulement lorsque les cas d'usage correspondants seront raccordés.
6. Introduire, uniquement si les mesures le justifient, des caches courts et invalidables pour les référentiels CCNS.
