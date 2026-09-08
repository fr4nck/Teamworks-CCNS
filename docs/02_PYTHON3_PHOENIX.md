# Teamworks — suivi Python 3 / wxPython Phoenix

**Mise à jour : 8 septembre 2026**

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

## Références

- `ROADMAP.md`
- `AGENTS.md`
- `docs/MATRICE_COMPATIBILITE.md`
- `docs/CI_POLICY.md`
- `docs/01_VANILLA_BUGFIX.md`
