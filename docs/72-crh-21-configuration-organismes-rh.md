# CRH-21 — Configuration des organismes et connexions RH

## Statut

Lot empilé sur **CRH-20**. Il rend enfin configurable depuis l'interface le catalogue d'organismes utilisé par l'onglet salarié « Protection sociale ».

La validation manuelle Windows de **0.9.1b** reste le verrou de qualification de la release. CRH-21 demeure un développement distinct : aucune fusion automatique n'est demandée et toute future pré-release issue d'un `master` intégrant ce lot devra être reconstruite et requalifiée.

## Objectif

CRH-20 sait enregistrer une affiliation, une dispense, une clôture ou une nouvelle période, mais exige qu'un organisme soit déjà configuré pour la structure. CRH-21 fournit la boucle fonctionnelle manquante sans introduire de credentials ni d'intégration réseau.

Le bouton **« Organismes RH… »** est accessible depuis l'onglet salarié. Il ouvre un gestionnaire de structure indépendant du salarié et permet de préparer les profils utilisés par tous les salariés de la base active.

## Données configurables

Un profil d'organisme contient uniquement :

- une famille : URSSAF, Net-entreprises, mutuelle, prévoyance, retraite complémentaire, OPCO, SPST ou France Travail ;
- un code interne stable ;
- un nom d'organisme ;
- une période d'effet facultative ;
- des références administratives non secrètes ;
- des liens vers des portails HTTP/HTTPS ;
- les capacités déclarées par le connecteur de référence correspondant.

Le code et la famille sont verrouillés lors d'une modification afin qu'une correction de libellé ou de portail ne change jamais l'identité métier du profil.

Il n'existe pas d'action de suppression dans ce lot. Un profil déjà référencé par l'historique salarié ne doit pas disparaître silencieusement.

## Frontière applicative

`StructureHrConnectionsRuntimeFactory` assemble :

1. l'identité opaque de la structure de la base Teamworks active ;
2. `TeamworksHrConnectionsRepository` ;
3. le registre des connecteurs manuels de référence CRH-08 ;
4. `StructureHrConnectionsService` CRH-10A ;
5. une façade qui ne demande jamais à l'interface de fabriquer `structure_ref`.

`StructureOrganizationProfileRequest` transporte seulement les données administratives saisies. La couche wxPython n'accède directement ni à `GestionDB`, ni au SQL, ni aux tables `tw_hr_*`.

## État d'un connecteur

Le gestionnaire affiche **Configuré** lorsqu'au moins un connecteur de la famille considère le profil local complet. Avec les connecteurs manuels actuels, cela signifie notamment qu'un portail est renseigné.

Un profil peut volontairement rester **À compléter** : il est alors enregistré comme organisme connu, sans prétendre que le connecteur est opérationnel.

## Références et portails

La première interface reste volontairement compacte :

- références : une ligne `type | valeur | libellé optionnel` ;
- portails : une ligne `libellé | https://adresse`.

Les objets de domaine `OrganizationReference` et `PortalLink` effectuent ensuite les contrôles existants, notamment le refus des références typées comme secrets et des URL contenant des identifiants intégrés.

## Sécurité et isolation

CRH-21 n'ajoute :

- aucun champ de mot de passe, jeton, clé API ou certificat ;
- aucun appel réseau ;
- aucune ouverture automatique de navigateur ;
- aucun scraping ;
- aucun calcul de paie ;
- aucune donnée médicale ;
- aucune migration destructive ;
- aucune suppression de profil.

Le dialogue de configuration n'est importé qu'après une action explicite de l'utilisateur. L'ouverture de la fiche salarié ne charge donc pas ce sous-système supplémentaire.

## Effet sur l'onglet salarié

Après fermeture du gestionnaire, la synthèse du salarié est rechargée et le runtime des actions est invalidé. Un organisme nouvellement configuré devient ainsi disponible sans redémarrer Teamworks.

Si la configuration des organismes échoue, l'erreur est isolée et la fiche salarié reste utilisable.

## Suite

Une fois ce lot qualifié, les étapes suivantes pourront enrichir le cockpit structure (échéances et démarches CRH-03/04) puis ajouter progressivement les échanges de fichiers ou API officielles lorsqu'ils existent réellement, sans transformer les portails web en automatisations fragiles.
