# Teamworks-CCNS — tableau de bord des quatre axes

**Mise à jour : 25 août 2026**

Ce document est un **tableau de lecture dérivé**, pas une roadmap concurrente. `ROADMAP.md` reste l'unique feuille de route officielle. Les méthodes de classement sont imposées par `AGENTS.md`.

## Vue synthétique

| Axe | Avancement | Nature du restant |
|---|---:|---|
| **Vanilla / Bugfix** | **75 %** | 7 correctifs confirmés, patches minimaux préparés et validés statiquement ; test runtime historique restant |
| **Python 3 / wxPython Phoenix** | **88 %** | qualification du portable exact de `master` et validation Windows réelle |
| **UI/UX / thème graphique** | **78 %** | migration/finitions des écrans historiques et validation visuelle réelle |
| **CCNS & extensions** | **83 %** | consolidation de quelques frontières d'architecture et surtout recette métier réelle |

## Lecture correcte des pourcentages

Ces valeurs ne mesurent pas toutes la même chose :

- Vanilla mesure l'avancement du **lot de correctifs historiques actuellement identifié** ;
- Python 3/Phoenix mesure la **migration technique** ;
- UI/UX mesure la **modernisation visuelle et ergonomique** ;
- CCNS mesure le **développement fonctionnel ajouté par le fork**.

Elles ne doivent donc pas être moyennées simplement.

## Avancement global Teamworks-CCNS

Le chantier Vanilla est un axe parallèle destiné à conserver une version historique corrigée utilisable pendant le développement ; il **n'entre pas dans le calcul d'avancement de Teamworks-CCNS moderne**.

Pour le produit moderne, pondération de lecture retenue :

- Python 3 / Phoenix : **25 %** du chantier ;
- UI/UX : **30 %** ;
- CCNS & extensions : **45 %**.

Calcul :

`(88 × 0,25) + (78 × 0,30) + (83 × 0,45) = 82,75`

**Avancement de développement Teamworks-CCNS : environ 83 %.**

Ce 83 % ne vaut pas qualification bêta/RC. Le projet reste en `0.9.0-dev` tant que le portable du SHA exact de `master` n'a pas été construit, parcouru sur Windows et testé sur une copie réelle de la base.

## État du chantier Vanilla

Une branche de préparation **`vanilla-bugfix`** a été créée à partir de la base originale commune :

`00bd52ef85853eb617361a15c2f0cc0cfa1b898e` — Teamworks 2.1.3.1.

Les backports minimaux sont conservés dans `patches/vanilla/`. Ils ont été appliqués sur une copie exacte du snapshot historique, passent `git apply --unidiff-zero --check`, compilent via `py_compile` et passent `git diff --check`.

Il reste le test réel dans l'environnement historique avant de considérer le lot Vanilla à 100 %.

## Fichiers détaillés

- `docs/01_VANILLA_BUGFIX.md`
- `docs/02_PYTHON3_PHOENIX.md`
- `docs/03_UI_UX_MODERNISATION.md`
- `docs/04_CCNS_EXTENSIONS.md`
- `patches/vanilla/README.md`

Les pourcentages sont recalculés uniquement lorsque l'état d'un jalon change réellement. Un commit, une CI verte ou une impression de progression ne suffisent pas à eux seuls à faire monter un axe.
