# Teamworks — suivi Python 3 / wxPython Phoenix

**Mise à jour : 16 septembre 2026**

## Objectif

Ce fichier suit uniquement la **migration technique** depuis le socle historique vers Python 3 et wxPython Phoenix.

Il ne doit pas contenir les bugs déjà présents dans Teamworks Vanilla, la modernisation graphique en tant que telle, ni les règles CCNS et fonctionnalités métier ajoutées.

## Règle de classement

- défaut déjà présent dans `Noethys/Teamworks` → `01_VANILLA_BUGFIX.md` ;
- code Vanilla fonctionnel dans son environnement historique mais incompatible avec Python 3/Phoenix → ce fichier ;
- régression introduite par le thème ou les nouveaux composants → `03_UI_UX_MODERNISATION.md` ;
- fonctionnalité nouvelle → `04_CCNS_EXTENSIONS.md`.

Les correctifs de parentage `StaticBox` rencontrés pendant les smokes Windows sont classés ici tant qu'aucune preuve ne montre qu'ils cassaient Teamworks dans son environnement wxPython historique.

## Méthode de mesure

La migration est découpée en **8 jalons de poids égal**. Un jalon n'est compté comme terminé que lorsque son résultat est réellement présent dans `master` et couvert par les validations correspondantes.

| Jalon | État | Preuve actuelle |
|---|---|---|
| 1. Sources Python 3 compilables | Terminé | CI #571 : **323/323 fichiers Python compilables** |
| 2. Unicode, UTF-8 et dates historiques | Terminé | lots TW-136+ intégrés ; politique UTF-8 et normalisation des dates dans la CI |
| 3. API wxPython Classic → Phoenix | Terminé au niveau automatisé | migrations wx, checklists Phoenix, doubles checkboxes supprimées, smokes dialogues |
| 4. Compatibilité données / SQL historique | Terminé au niveau automatisé | compatibilité MySQL/MariaDB historique conservée ; **0 chemin SQLite binaire** dans la qualification |
| 5. Tests Linux du socle migré | Terminé | CI #571 : **1 785 tests pytest réussis** |
| 6. Parcours critiques Windows / wxPython 4.3.1 | Terminé au niveau automatisé | parcours critiques Windows réussis sur la qualification post-TW-189 |
| 7. Packaging Python 3 reproductible | Terminé côté infrastructure | pipeline PyInstaller, manifeste, `BUILD.txt`, SHA-256, smoke de l'exécutable ; build seulement sur demande/tag |
| 8. Qualification du portable exact de `master` sur machine réelle | À faire | le portable correspondant au `master` consolidé n'est pas encore construit et validé manuellement |

## Avancement

7 jalons terminés sur 8 :

**Python 3 / wxPython Phoenix : 87,5 %, arrondi à 88 %.**

Ce pourcentage mesure la **migration technique**, pas la maturité d'une release. Le dernier jalon est volontairement lourd : il comprend la construction du portable depuis le SHA exact puis la validation réelle Windows sur une copie de base.

## Restant prioritaire

1. construire le portable Windows depuis le `master` exact à qualifier ;
2. vérifier archive, manifeste, `BUILD.txt`, sommes SHA-256 et démarrage ;
3. exécuter le parcours Windows minimal réel ;
4. reclasser toute anomalie rencontrée : Vanilla, Python/Phoenix, UI/UX ou CCNS avant correction.

Le build manuel du 28 août a confirmé une anomalie de packaging Python 3 :
avec un `--specpath` distinct, PyInstaller résolvait le chemin relatif de
l'icône depuis le dossier du fichier `.spec`. Le workflow utilise désormais le
chemin absolu résolu avant l'appel à PyInstaller, avec un test de contrat dédié.

## Recette Windows 0.9.2 RC1 — correctifs techniques préparant RC2

La recette réelle du 8 septembre 2026 a révélé deux incompatibilités techniques
qui n'étaient pas correctement couvertes par les smokes automatisés :

- le publipostage utilisait encore `Thread.isAlive()`, supprimé en Python 3
  moderne, derrière un `except` silencieux. Le garde pouvait donc laisser partir
  un second worker alors que le premier possédait encore des proxies COM. Le
  flux manipulait en outre des contrôles wx depuis ce worker et pouvait fermer
  Word/Writer au milieu d'une opération. Le correctif RC2 impose un worker
  propriétaire unique de l'automatisation, une annulation coopérative, des
  mises à jour UI via `wx.CallAfter` et une libération COM unique dans le thread
  propriétaire ; la disparition du crash natif reste à confirmer en recette
  Windows réelle avec Word/Writer ;
- la saisie des champs de publipostage transmettait directement des colonnes SQL
  nullables à `wx.TextCtrl.SetValue()`. Phoenix exige une chaîne : les valeurs
  `NULL` sont désormais normalisées avant l'appel wx et couvertes par un test de
  non-régression.

Qualification automatisée dédiée au commit applicatif RC2 : compilation ciblée,
**11 tests passés / 2 ignorés sous Linux** et **13 tests passés sous Windows
Server 2022 avec wxPython 4.3.1**. Cette qualification ne lance aucun packaging
et ne remplace pas la recette Word/COM réelle.

## Recette Windows 0.9.2 RC3 — updater historique neutralisé

La recette Windows réelle du 16 septembre 2026 a reproduit un `ValueError` dans
`DLG_Updater.ConvertVersionTuple()` avec la version locale `0.9.2-rc3` : le
parseur hérité de Teamworks convertissait chaque composant séparé par un point
en entier et ne connaissait donc pas les suffixes de prérelease `-rcN`.

L'audit du module a également confirmé que ce même parcours utilisait encore
les services de mise à jour historiques Teamworks/Noethys et pouvait télécharger
un ancien paquet Teamworks. Le dépôt Teamworks-CCNS possède des releases GitHub,
mais aucun protocole d'auto-mise-à-jour applicatif n'est encore qualifié pour la
RC3 (canal de release, intégrité, téléchargement, installation et relance).

Décision RC3 : **désactiver proprement l'updater hérité** plutôt que de le rendre
compatible avec le nouveau numéro de version tout en conservant une source de
mise à jour obsolète. Le dialogue conserve son point d'entrée utilisateur,
affiche la version locale issue du fichier canonique `VERSION`, indique que la
mise à jour automatique n'est pas encore disponible et n'effectue aucun accès
réseau ni téléchargement.

Le parseur commun accepte explicitement `X.Y.Z` et `X.Y.Z-rcN` et impose
l'ordre `rc1 < rc2 < ... < version finale`. Les formats inconnus restent rejetés
par le parseur, tandis que le lecteur utilisé par l'interface transforme un
fichier `VERSION` absent ou invalide en état « version locale inconnue » sans
exception UI non interceptée.

La correction reste à qualifier sur un nouvel EXE Windows réel avant de pouvoir
considérer le défaut RC3 comme fermé.

## Qualification du 9 octobre 2026 — locale native partagée

Le run post-fusion de la PR #430 (`37907756088`, commit `6024750e`) a confirmé
un crash natif intermittent lors du cycle modal de la fiche personne. Une
relance du job Windows n'a pas validé le bilan. Localement, dix processus de
cinq cycles passaient, puis un processus prolongé a reproduit le crash dès
le troisième cycle : une relance verte isolée ne prouve donc pas la correction.

Le défaut de durée de vie est hérité de Vanilla : voir
`01_VANILLA_BUGFIX.md` pour la comparaison amont et le backport. La locale
native est désormais conservée par l'application wx et partagée entre les
six fenêtres/listes concernées. Aucun callback ni contrôle n'est désactivé.
La documentation wxPython décrit le risque de crash si des locales natives
se chevauchent : https://docs.wxpython.org/internationalization.html.

Qualification locale : Windows 11, Python 3.10.11, wxPython 4.3.1 /
wxWidgets 3.3.3 ; un passage de 50 cycles puis trois passages supplémentaires
de 50 cycles réussis, avec création du canari natif après chaque destruction ;
24 tests ciblés réussis. Le smoke CI passe de 5 à 20 cycles et un garde-fou
AST interdit les créations de locale natives hors du propriétaire partagé.
La CI Python 3.11 Linux/Windows et la recette EXE restent des niveaux distincts.

## Références

- `ROADMAP.md`
- `AGENTS.md`
- `docs/MATRICE_COMPATIBILITE.md`
- `docs/CI_POLICY.md`
- `docs/01_VANILLA_BUGFIX.md`
