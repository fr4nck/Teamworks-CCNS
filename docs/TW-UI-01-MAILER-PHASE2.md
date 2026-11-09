# TW-UI-01 — Phase 2 : transports et fenetres de messagerie wx

Date : 9 novembre 2026. Branche : `wx/master`.
Cette fiche est technique ; `ROADMAP.md` reste la seule roadmap officielle.

## Reference du prevol

- `master` : `308967df490b50555f82d6975e47efc10c65e687`
- `qt/master` : `d2bdebf92315d2873121710ae56ec35ac4d869ae`
- `wx/master` au debut : `743ab967e3d277d2697a43d210d38e44b08d1737`
- CI du point de depart : run `42602019520`, Linux et Windows SUCCESS.
- Corrections initiales : `f7f58c0` et `743ab96`.

## Cartographie des transports

| Point d'entree | Chemin | Comportement retenu |
| --- | --- | --- |
| Mailer visible et envoi test | `DLG_Mailer.Dialog.Envoyer` | `envoyer_avec_progression` ; transport dans un worker |
| Mailer cache / famille | `UTILS_Envoi_email.EnvoiEmailFamille(visible=False)` | Retour synchrone, progression appartenant a une fenetre visible |
| Mailer d'export | `UTILS_Export` -> `DLG_Mailer.Dialog` | Dialogue rattache a la fenetre principale |
| Backend SMTP historique | `SmtpV1.Envoyer_lot` herite de `Base_messagerie` | Adaptateur vers session unique, liste de succes conservee |
| Backend SMTP | `SmtpV2.Envoyer_lot` herite de `Base_messagerie` | Ancienne boucle supprimee |
| Test de configuration de messagerie | `DLG_Saisie_email_exp_legacy.OnBoutonTester` | Reutilise le worker commun, exige un resultat accepte |
| Backend Mailjet | `Mailjet.Envoyer_lot` herite de `Base_messagerie` | Ancienne boucle supprimee |
| Sauvegarde par email | `UTILS_Sauvegarde.Sauvegarde` | Un message, transport en worker, bilan positif obligatoire |
| Rapport de crash | `UTILS_Envoi_rapport_bug.EnvoyerRapport` | Worker si boucle wx presente ; moteur pur sinon |

Le garde-fou `tests/test_tw_ui_01_mailing_phase2.py` parcourt les fichiers
`teamworks/**/*.py` et signale les nouveaux constructeurs de messagerie
et les nouveaux appels directs a `Envoyer_lot`. Il constitue un inventaire
dynamique des sources, pas une preuve suffisante pour les importations
reflexives ou le code charge hors depot.

Les operations de validation des adresses, de fusion et de selection
prealables a la transmission restent sur leurs appels historiques.

## Invariants

- Transport unitaire/sequentiel, aucun renvoi automatique apres erreur de
  transmission dont l'issue est inconnue.
- Acceptation positive limitee a `True`, entier strictement positif
  (contrat SMTP), ou texte exact `success` (contrat Mailjet).
- `False`, `0`, `None` et toute autre reponse non documentee ne valent pas
  acceptation.
- Exceptions pendant `Envoyer` -> `incertains`, sans nouvelle tentative.
- Etat `non_tentes` pour les messages restants si le lot s'arrete.
- Etat du message accepte conserve si la fermeture du transport echoue.
- Les anciens `Envoyer_lot` ont les memes arguments et renvoient une liste
  de messages acceptes ; le detail figure dans `dernier_bilan`.
- La connexion du backend historique reste geree par l'appelant :
  `Connecter` avant `Envoyer_lot`, `Fermer` apres.
- Aucune creation/manipulation de widget sur le worker ; synchronisation
  par `wx.CallAfter`.
- Fenetre de progression non fermable par Esc/fermeture classique pendant
  le transport, pour eviter les callbacks vers une fenetre detruite.
- Dialogues `DLG_Messagebox` avec parent explicite sans
  `DIALOG_NO_PARENT` / `STAY_ON_TOP`. Le mode legacy sans parent reste
  conserve, faute d'inventaire complet de tous ses consommateurs.
- Aucune modification SQL, donnees RH reelles, envoi externe ni publication.

## Tests

`tests/test_tw_ui_01_mailing_worker.py` et
`tests/test_tw_ui_01_mailing_phase2.py` couvrent les issues du moteur pur,
les reponses positives et negatives SMTP/Mailjet, les deconnexions,
l'absence de renvoi, les connexions pre-ouvertes, une fausse boucle wx
reactive et la garde statique des appels. La fausse boucle wx teste
la separation des threads mais **ne teste pas les HWND Windows reels**.

La CI doit aussi conserver les tests existants sauvegarde, rapport de
crash, interfaces, permissions, compilation et packaging policy.

## Banc Windows natif fictif

Le script `tools/smoke_tw_ui_01_mailer_windows.py` est ajoute au job
Windows existant (pas de nouveau workflow et pas de packaging). Il cree
une vraie `wx.Frame` maximisee et une progression `wx.Dialog` rattachee,
utilise un backend fictif lent et mesure pendant l'envoi :
- retard entre les battements de timer wx ;
- `IsMaximized` / `IsIconized` / `IsHungAppWindow` ;
- propriete wx du dialogue et relation Win32 `GW_OWNER` ;
- execution du transport hors du thread GUI et tentative unique.

Il n'utilise ni base, ni SMTP, ni Mailjet reels. Son verdict CI Windows
est distinct d'une recette utilisateur de l'application complete.

## Qualification effectivement observee

- Code qualifie : `959fd504a7a6629131d871d1dfe51ba5ee09b1e1`.
- CI : https://github.com/fr4nck/Teamworks-CCNS/actions/runs/42613561411
- Linux : 2 882 PASS, 12 SKIP, un avertissement ; compilation et autres
  gardes du socle PASS.
- Windows : job parcours critiques PASS ; banc `TW_UI01_WINDOWS_PASS`
  avec 23 battements pendant le transport fictif, retard maximal de
  0,032 seconde, proprio wx et `GW_OWNER` corrects, fenetre maximisee
  sans iconisation et `IsHungAppWindow` faux durant les observations.
- Repetitions : une connexion et une emission fictives ; aucune
  transmission reseau ni donnees RH.
- Ces observations concernent une vraie fenetre wx Windows sur runner
  GitHub, et non l'application utilisateur connectee a une base.

## Limites et gates de validation

1. **Non demontre** : une fenetre fantome ou perte effective de maximisation
   dans Teamworks sur Windows.
2. **A effectuer** : test wx natif instrumente pendant SMTP et Mailjet
   simules, avec etats `IsMaximized`, `IsIconized`, `GW_OWNER` et
   `IsHungAppWindow` pendant l'operation (pas uniquement apres).
3. **A effectuer** : recette Mailer cache/visible, backup et rapport de crash
   dans une copie de profil sans donnees metier et sans destinataire reel.
4. **A verifier** : comportement des bibliotheques SMTP/Mailjet lors de
   deconnexions a des etapes differentes ; le timeout avant ou apres
   emission reste classe par prudence `incertain`.
5. **A verifier** : innocuite des lectures de parametres par les workers
   sur les configurations historiques et environnements MySQL.
6. **Hors du lot** : operations longues non liees a l'envoi de messages
   (exports, impressions, SQL, autres progressions).

La compilation et la CI doivent etre recontrolees sur le commit final.
La validation interactive Windows et la recette utilisateur restent
des gates distincts. Aucun packaging ni release par ce lot.

## Classification et repli

Le code est herite de Teamworks/Noethys, mais la presence exacte du defaut
dans l'amont Vanilla n'a pas ete confirmee. Classification provisoire :
**candidat Vanilla / bugfix**, avec adaptation wxPython Phoenix a confirmer.

Retour arriere : revisions et arbres Git conserves ; ne pas supprimer
d'etat utilisateur. Revenir par revert cible si une regression runtime est
demontree ; jamais par force-push.
