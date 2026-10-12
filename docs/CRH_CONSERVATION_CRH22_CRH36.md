# Conservation des apports CRH-22 et CRH-36

Le candidat reprend les protections de CRH-36 et conserve l'accès salarié et les textes longs de CRH-22. Le socle partagé est porté sur master ; le raccord salarié est porté séparément sur wx/master en conservant ses correctifs actuels de fermeture et de généralités.

## Schéma des démarches RH version 2

Sur MySQL/MariaDB, les colonnes `result`, `comment` et `field_value` utilisent TEXT ; `document_label` utilise VARCHAR(240). Les variantes connues de la version 1 sont élargies sans réduire les valeurs. L'index organisme inclut l'échéance et l'index redondant d'audit `idx_tw_hr_events_target` est retiré après création de `idx_tw_hr_audit_target`.

Sur SQLite, les colonnes TEXT/VARCHAR ont la même affinité et aucune limite de longueur ; les tables et leurs données restent en place. La version et les index sont normalisés sans reconstruire les tables pour modifier seulement leur métadonnée de type.

La migration refuse une version future, des colonnes/types/contraintes/clés inattendus et, sur SQL réseau, un moteur différent d'InnoDB. Elle sérialise les appels du nouveau code par `BEGIN IMMEDIATE` sur SQLite ou verrou MySQL nommé, limité au composant et à la base. Ces verrous ne coordonnent pas un ancien binaire version 1 exécuté simultanément : il faut fermer les anciennes instances avant une migration réelle.

Le DDL MySQL/MariaDB peut valider implicitement une étape. La version 2 n'est enregistrée qu'après toutes les étapes ; un état partiellement élargi de version 1 est accepté pour reprendre une migration interrompue. Une sauvegarde de la base réelle reste nécessaire avant portage ; retourner à l'ancien code exige restaurer sa copie de base, car il refuse la version 2.

TEXT garde les limites du serveur et de son encodage : ce changement ne promet pas des chaînes de longueur illimitée ni le support utf8mb4 sur les bases historiques utf8.

## Configuration et parcours salarié

La famille d'un organisme existant reste immutable et ses capacités déjà qualifiées sont conservées. Un nouveau profil reçoit uniquement les capacités réellement déclarées par le connecteur manuel de référence. OTHER est autorisé sans connecteur ni capacités ; aucun transport API ou automatisé n'est inventé.

Le bouton « Organismes RH… » ouvre paresseusement `DLG_Organismes_connexions_rh`. Après fermeture, le runtime d'actions est invalidé avant le rechargement du suivi salarié. L'ancien dialogue CRH-22 et son ancien contrat de demande ne sont pas réintroduits : leurs seuls consommateurs historiques utilisaient ce dialogue remplacé. Le nouveau raccord utilise le contrat CRH-36.

## Transactions et erreurs

Les violations de clé unique sur la création d'un dossier ou d'un événement sont converties en erreurs métier après rollback. Une collision ne laisse pas de projection, de pièces ou d'audit partiel. Deux transitions sur le même statut initial ne valident qu'une modification avec son audit ; le second appel reçoit l'erreur d'état périmé.

Le repository générique `save_case` reste une sauvegarde de projection sans version optimiste et peut écraser une lecture ancienne. Les actions utilisateur doivent utiliser les adaptateurs création/workflow/pièces. Aucun retry automatique sur deadlock n'est ajouté : la transaction échoue, et la politique de retry doit être qualifiée avec l'opération métier concernée.

## Qualification

Les tests de migration exercent les deux schémas version 1 avec des données existantes, les textes longs, l'idempotence, les schémas inattendus et les versions futures. Les tests réseau utilisent deux instances jetables séparées des bases utilisateur : MySQL 5.5.62 et MariaDB 10.11.14, InnoDB et utf8, connecteur 9.7.0 en mode Python pur et mode SQL strict.

Les tests de concurrence utilisent deux connexions et des threads, avec synchronisation du contrôle préalable des collisions. Ils couvrent l'initialisation, les doublons d'audit, les collisions dossier/événement de création, les transitions concurrentes et le rollback sur erreur tardive. La reprise après DDL interrompu et le refus de MyISAM sont testés sur les deux serveurs réseau.

Le test wx natif utilise wxPython 4.3.1 / wxWidgets 3.3.3 sous Windows, une configuration isolée, une base SQLite jetable et le bootstrap visuel chargé avant le panneau. Il exerce cinq ouvertures/fermetures modales, les parents des groupes, le rechargement et l'invalidation du cache. Le portage dans l'application courante et la recette utilisateur sur copie réelle restent distincts de cette qualification.


## Qualification du portage permanent

Les portages sont construits depuis master `47a3bf07` et wx/master `c6dabe16`, sans reprise des 230 commits historiques. Les exports existants des packages sont conservés. Aucun dépôt DPAE, Sorties salarié ou Session RH existant n'est remplacé.

Le lot wx ajoute seulement les panneaux Protection sociale, les dialogues d'action et de configuration des organismes, l'onglet différé en fin de fiche et le menu des organismes. Les écrans cockpit, création, workflow, historique et pièces sont désormais raccordés dans un lot wx distinct, avec leur menu chargé à la demande. Qt n'est pas modifié.

Sur les arbres finaux du portage : 278 tests passent pour le socle master et 325 pour wx, sous Windows et Linux ; les deux tests réservés au moteur SQL sont ignorés dans ces suites SQLite. Les 12 tests réseau passent sur chacun des serveurs jetables MySQL 5.5.62 et MariaDB 10.11.14. Le vrai événement du bouton Organismes RH est exercé sur cinq cycles modaux wx natifs avec rechargement et invalidation du cache d'actions.

Cette qualification est locale et ciblée. Aucune CI distante, construction de paquet ou recette sur base utilisateur n'est revendiquée. Les raccordements wx de CRH-36 sont maintenant portés localement. Aucune branche distante ne doit être supprimée avant publication des commits locaux, vérification des SHA distants et accord distinct de suppression.


## Qualification des écrans de démarches

Les six tests métier omis par un classement trop large du mot teamworks sont présents sur master et wx/master. Le socle partagé passe 319 tests sous Windows et Linux. Les écrans sont testés avec tous les tests CRH, les gardes de fermeture différée et de durée de vie de locale, et les tests de compatibilité du snapshot de salaire existant.

Le test natif traverse trois fois création, préparation, réception/retrait d'une pièce, historique, transmission déclarée et acceptation. Chaque dossier conserve six événements réels sur une base SQLite jetable, avec le statut technique d'échange inchangé. Une confirmation annulée n'écrit rien ; une modification concurrente empêche la transition depuis une projection périmée ; les pièces d'un dossier accepté restent en lecture seule. Les confirmations sont automatisées via wx.GenericMessageDialog, tandis que les formulaires et événements des boutons sont réels.

Les erreurs de rafraîchissement après création, transition, réception ou retrait affichent désormais que l'action est enregistrée et invalident la projection/action périmée. Ces scénarios sont injectés après les écritures réelles, puis vérifiés dans la base et l'interface. Les erreurs d'écriture conservent leur signalement séparé.

Les documents historiques CRH-17B à CRH-36 restent disponibles sous le tag d'archive exact de la branche CRH-36 ; leur absence dans le rail ne signifie pas perte de contenu. Cette synthèse décrit les contrats actuels, notamment le schéma version 2, au lieu de réintroduire leurs anciens états version 1.
