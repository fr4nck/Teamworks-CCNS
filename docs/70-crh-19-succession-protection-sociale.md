# CRH-19 — Succession atomique des périodes de protection sociale

## Statut

Lot empilé sur **CRH-18**. Il ferme le principal trou fonctionnel avant l'ajout de dialogues d'écriture wxPython : une modification structurante d'un suivi salarié peut désormais être représentée par deux périodes historisées sans état intermédiaire partiellement enregistré.

La validation manuelle Windows de **0.9.1b** reste le verrou de qualification de la release. CRH-19 reste un lot satellite isolé ; s'il rejoint `master`, le build correspondant devra être reconstruit et requalifié.

## Problème traité

CRH-18 permettait de clôturer une période et d'en créer une nouvelle, mais ces deux écritures auraient produit deux commits distincts si l'interface les enchaînait directement. Une panne ou une erreur sur la seconde écriture pouvait donc laisser le salarié avec une période clôturée sans période successeure.

CRH-19 ajoute une opération métier explicite : `supersede()`.

## Règle métier

Une succession :

- part d'un suivi `ACTIVE` existant ;
- exige une nouvelle période `ACTIVE` avec une date d'effet explicite ;
- attribue un **nouvel identifiant opaque** à la période successeure ;
- clôture la période précédente la veille de la nouvelle date d'effet ;
- produit donc deux périodes contiguës, sans chevauchement ;
- refuse une date d'effet identique ou antérieure à celle de la période active ;
- refuse de prolonger artificiellement une période qui possède déjà une date de fin plus proche ;
- autorise un changement d'organisme, de régime, d'option, de profil de cotisation ou de nature de lien uniquement si le nouveau `EmployeeProtectionRecord` respecte les invariants du domaine ;
- exige que l'organisme de la nouvelle période soit configuré pour la structure.

L'ancien organisme peut avoir disparu de la configuration courante : son historique reste clôturable et lisible.

## Transaction de production

`TeamworksEmployeeProtectionSuccessionRepository` étend l'adaptateur CRH-16 sans ajouter de table ni modifier le schéma.

Dans une seule connexion `GestionDB` :

1. la période courante est relue ;
2. son statut `ACTIVE`, son salarié, sa date d'effet et ses métadonnées stables sont contrôlés afin de détecter une donnée devenue obsolète entre lecture et écriture ;
3. la ligne précédente est mise à jour en `ENDED` ;
4. la période successeure est insérée par un `INSERT` strict ;
5. le commit n'intervient qu'après réussite des deux écritures.

Toute exception déclenche un rollback. En particulier, une collision de clé sur la nouvelle période annule aussi la clôture déjà exécutée dans la transaction.

L'adaptateur conserve le contrat SQLite/MySQL historique du module CRH-16 : placeholders adaptés selon `isNetwork`, commit via `GestionDB.Commit()` et rollback sur la connexion sous-jacente.

## Frontière applicative

`EmployeeProtectionService.supersede()` valide la paire de périodes puis délègue l'unité de travail atomique au repository. Il ne réutilise pas deux appels successifs à `save()`.

`EmployeeProtectionActionService.supersede()` construit la paire depuis le contexte salarié :

- période précédente = copie de l'enregistrement actif, statut `ENDED`, fin = veille de la nouvelle date d'effet ;
- période successeure = nouvelle instance, nouvel identifiant, données fournies par `EmployeeProtectionCreateRequest`.

Le résultat `EmployeeProtectionSuccessionResult` expose séparément les deux vues historisées.

## Runtime

`EmployeeProtectionActionsRuntimeFactory` utilise désormais `TeamworksEmployeeProtectionSuccessionRepository`. La façade verrouille toujours `structure_ref` sur l'identité de la base Teamworks active et expose `register()`, `end()` et `supersede()`.

Aucune logique de transaction n'est portée par wxPython.

## Garde-fous

CRH-19 n'ajoute :

- aucune migration ni table ;
- aucune suppression de ligne ;
- aucune édition libre de l'historique ;
- aucun calcul de cotisation ou de paie ;
- aucune donnée médicale ;
- aucun secret ;
- aucun appel réseau ou automatisation de portail ;
- aucun nouveau bouton dans la fiche salarié.

Les tests couvrent notamment la continuité des périodes, le changement d'organisme/profil, la disparition de l'ancien profil d'organisme, les dates invalides, la détection d'un prédécesseur devenu obsolète et surtout le **rollback intégral** si l'insertion de la période successeure échoue.

## Suite proposée

La prochaine étape peut être l'interface d'écriture wxPython de l'onglet salarié : création, dispense, clôture et succession de période. Cette interface devra rester mince, rafraîchir la synthèse après succès et conserver le garde-fou CRH-17B : une erreur Connexions RH ne doit jamais rendre la fiche salarié inutilisable.
