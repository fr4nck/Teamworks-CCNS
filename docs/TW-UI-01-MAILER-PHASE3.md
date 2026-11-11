# TW-UI-01 / Phase 3 — qualification des transports et de Windows

**Date :** 9 novembre 2026
**Rail :** `wx/master`
**Nature :** preuve technique, distincte de la roadmap officielle `ROADMAP.md`.
**Aucun serveur, compte, identifiant ou destinataire de production utilisé.**

> **Note de suivi (11 novembre 2026) :** ce rapport décrit l'état de la **phase 3 au 9 novembre**, avant la publication. La [préversion RC12 a été publiée](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12) depuis le commit `9b02fbe9`, après CI `42675793471` et essai de démarrage Windows 11 confirmé. Les mentions ci-dessous « pas de RC publiée » ne sont donc plus le statut courant ; les réserves de recette Mailer et de stabilité demeurent. Source de vérité : [ROADMAP](../ROADMAP.md).

## 1. Référence et périmètre

Au prévol :
- `wx/master` : `b48c6104d3bed798df097d04e365823999e8acb7`
- `master` : `308967df490b50555f82d6975e47efc10c65e687`
- `qt/master` : `d2bdebf92315d2873121710ae56ec35ac4d869ae`
- Dernière CI initiale : `42614069876`, SUCCESS,
  2 882 PASS, 12 SKIP, validation Windows native PASS.

Correctifs de Phase 3 :
- `711549ce9705725142808e4474dfcd383a0d4168` : refuser un statut
  JSON Mailjet « success » si HTTP ne confirme pas l'acceptation ; tests
  directs des classes `SmtpV1`, `SmtpV2`, `Mailjet` avec réseau simulé.
- `0b1316156ea66d03fa2c3f0746c57dfd906c1963` :
  fermeture de la progression explicitement non assimilée à une annulation,
  banc natif Windows du cycle de vie, intégré au workflow CI unique.

## 2. Qualification du moteur d'envoi

Les tests de `tests/test_tw_ui_01_transport_phase3.py` compilent depuis
l'AST les **classes applicatives originales**, au lieu de recopier les
implémentations dans les tests. Ils substituent uniquement les connexions
et objets de transport (sans ouvrir de connexion réelle).

| Contrôle | Preuve / critère |
| --- | --- |
| SMTP V1 : retour vide de `sendmail` | Un message accepté, une transmission |
| SMTP V1 : destinataires partiellement refusés | Message incertain, aucun renvoi |
| SMTP V1 : déconnexion durant `sendmail` | Message incertain, aucune reprise implicite |
| SMTP V1 : échec d'authentification | Aucun message transmis |
| SMTP V2 : retour de `EmailMultiAlternatives.send` | 0 non accepté ; 1 accepté |
| Mailjet : HTTP 200/201 avec JSON `success` | Acceptation enregistrée |
| Mailjet : HTTP 400/429/500 malgré JSON `success` | Aucun succès enregistré |
| Mailjet : réponse JSON négative ou malformée | Incertitude conservée |
| Mailjet : timeout lors de l'envoi | Aucun renvoi, statut incertain |

L'absence de renvoi automatique est garantie par l'orchestration commune
`UTILS_MailingSession.envoyer_lot_sans_wx`.

**Limites :** ces tests n'exercent pas les sockets SMTP ni le SDK Mailjet
jusqu'à un vrai serveur local HTTP/SMTP. Les erreurs DNS, TLS, serveur
réel, interruption physique de réseau et livraison finale ne sont pas
démontrées par ces tests ; ces gates restent ouverts.

## 3. Cycle de vie de la progression wx

Les scripts `tools/smoke_tw_ui_01_mailer_windows.py` (Phase 2) et
`tools/smoke_tw_ui_01_windows_lifecycle.py` (Phase 3) exercent des
**objets wx natifs sous Windows** avec transports entièrement fictifs.

Le banc Phase 3 :
- démarre une fenêtre wx en mode fenêtré ;
- déclenche une transmission fictive lente dans un worker ;
- tente `Close()` sur le dialogue de progression **pendant** l'envoi ;
- vérifie que le dialogue reste modal et visible ;
- vérifie qu'un seul message fictif est traité ;
- vérifie la disparition finale du dialogue et l'absence de worker vivant ;
- vérifie que la fenêtre n'est pas artificiellement maximisée ;
- lit `GetWindowPlacement` et `GetForegroundWindow` (ce dernier
  à titre de diagnostic, sans forcer le premier plan) ;
- demande une iconisation volontaire après le traitement et un retour
  en mode fenêtré, sans prétendre reproduire un changement d'application
  par l'utilisateur pendant un réseau lent.

Un délai de 12 secondes est prévu pour arrêter le banc en cas de blocage.
La fermeture d'une progression active ne constitue pas une annulation
de transmission ; l'interface l'explique sans créer une autre modalité.

**Limites :** ces bancs ne constituent ni une recette de l'application
Teamworks complète, ni une preuve sur un bureau utilisateur à plusieurs
applications, ni une vraie interruption SMTP/Mailjet.

## 4. Protocole de recette fonctionnelle encore nécessaire

A effectuer sur un poste Windows 11 isolé, un profil vierge et une base
**fictive**, sans comptes de messagerie réels ni aucune donnée RH :
1. Installer/démarrer un candidat portable identifié par son SHA ; confirmer
   qu'aucun profil existant ni base de production n'est utilisé.
2. Mailer visible : sélection expéditeur fictif, objet, destinataire fictif,
   texte, puis réponse positive et négative injectée dans le transport.
   Contrôler les confirmations, la liste de succès et l'absence de doublon.
3. Mailer caché via `EnvoiEmailFamille(visible=False)` : vérifier le parent
   de la progression et le résultat synchrone ; aucun dialogue masqué.
4. Tester l'envoi collectif fictif, les pièces jointes de test et le
   retour en cas de statut incertain.
5. Tester « Tester l'adresse », export Excel vers Mailer, sauvegarde
   par mail et rapport de crash avec un transport fictif.
6. Répéter avec la fenêtre maximisée, puis fenêtrée ; changer d'application
   pendant l'attente et tenter volontairement de minimiser/fermer.
7. Relever pendant le traitement `IsMaximized`, `IsIconized`,
   `GetWindowPlacement`, `GetForegroundWindow`, `GW_OWNER`,
   `IsHungAppWindow`, latences du timer, résultat et threads encore actifs.
8. Vérifier les cas d'erreur et d'arrêt du worker sans jamais forcer une
   relance automatique. Les tests de fermeture ne doivent pas détruire une
   connexion à état d'envoi inconnu.

Toute reproduction doit consigner l'heure, le scénario fictif, la
révision exacte et le verdict ; aucun mot de passe, aucune adresse RH réelle.

## 5. Mesures, CI et gates pour la prochaine RC wx

Dernier HEAD de **code** validé :
`4adbcd192e53e4d178b886edec96dfe55ef6e00f`

GitHub Actions :
https://github.com/fr4nck/Teamworks-CCNS/actions/runs/42664772427

- Linux : **2 900 PASS, 12 SKIP, 1 avertissement** ; compilation et
  contrôles statiques réussis.
- Windows : parcours critiques PASS, banc de progression de la Phase 2 PASS,
  nouveau banc de fermeture de Phase 3 PASS.
- Progression : 23 battements, retard maximal de 0,032 seconde ;
  HWND/owner corrects ; la fenêtre reste maximisée sans blocage observé.
- Nouveau banc : fermeture active vetoée ; zéro worker encore vivant après
  l'envoi fictif ; zéro fenêtre résiduelle **après retour de l'event loop** ;
  iconisation volontaire possible, retour à la fenêtre normale ;
  `GetWindowPlacement` = 1 avant et après.
- Le premier essai de ce nouveau banc (`0b131615`) échouait car il
  recherchait une fenêtre résiduelle immédiatement après `Destroy()`.
  Le contrôle a été repris au cycle d'événements suivant (`4adbcd19`)
  pour respecter la destruction différée native de wx. Le critère
  d'absence de dialogue après retour à la boucle graphique est maintenu.
- Ni envoi réel, ni base RH réelle, ni mot de passe de production.

Les statuts ci-dessous désignent **uniquement le périmètre de preuve**.
Un PASS sur banc fictif ne vaut jamais PASS sur l'application complète.

| Gate | Exigence | Statut | Justification |
| --- | --- | --- | --- |
| G1 | Compilation et contrôles statiques | PASS | CI du SHA ci-dessus |
| G2 | Tests et régressions | PASS | 2 900 PASS, 12 SKIP |
| G3 | SMTP V1/V2 avec réseaux simulés | PASS | Méthodes applicatives AST exercées |
| G3 bis | Sockets SMTP/TLS/DNS et coupures réelles | NON TESTÉ | Pas de serveur local instrumenté |
| G4 | Mailjet avec réponses API simulées | PASS | HTTP/JSON et timeout simulés |
| G4 bis | Serveur HTTP local et SDK installé | NON TESTÉ | SDK HTTP réel non instrumenté |
| G5 | Progression et HWND wx natifs fictifs | PASS | Owners, maximisation, 23 battements |
| G5 bis | Focus et minimisation pendant le Mailer complet | NON TESTÉ | Bureau utilisateur non disponible |
| G6 | Fermer pendant transport fictif | PASS | Veto, fermeture différée, aucun worker |
| G7 | Parcours métier dans l'application installée | NON TESTÉ | Profil de recette non exécuté |
| G8 | Commits et CI traçables | PASS | Runs et HEAD liés |
| G9 | Recette utilisateur | NON TESTÉ | Aucun GO utilisateur recueilli |

**GO technique borné** aux corrections de transport et aux bancs testés.
**NO GO pour publication RC** : les parcours G7, G9 et les conditions
complémentaires de G3/G4/G5 ne sont pas acquises. Aucun tag ni release
ne doit être publié sur cette seule validation.

## 6. Publication ultérieure et limites maintenues

Depuis ce rapport daté du 9 novembre, la [RC12](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12) a été **publiée comme préversion le 11 novembre 2026**, commit `9b02fbe9`, sur des binaires qualifiés par la CI `42675793471`.

Le **NO GO du rapport du 9 novembre** signifiait que la phase 3 seule ne suffisait pas à justifier une release. La publication de la préversion a été décidée séparément après construction du paquet et essai de démarrage utilisateur. Cela **ne lève pas** les gates G3 bis, G4 bis, G5 bis, G7 et G9 en tant que recette complète ; `v0.9.2` stable reste non qualifiée.


## 7. Provenance et retour arrière

Le code historique SMTP/Mailer est un **candidat** à un correctif Vanilla,
mais l'origine exacte du défaut dans `Noethys/Teamworks` reste
non établie. Les différences Phoenix et les ajouts wx sont à qualifier
avant tout backport. Aucune modification dans `master` ou `qt/master`.

Retour arrière : revert ciblé des commits de Phase 3 après revue, pas de
force-push ; conserver les preuves et fichiers utilisateur inchangés.
