# Teamworks-CCNS — tableau de bord des quatre axes

**Mise à jour : 25 août 2026**

Ce document est un **tableau de lecture dérivé**, pas une roadmap concurrente. `ROADMAP.md` reste l'unique feuille de route officielle. Les méthodes de classement sont imposées par `AGENTS.md`.

## Vue synthétique

| Axe | Avancement | Nature du restant |
|---|---:|---|
| **Vanilla / Bugfix — audit exhaustif** | **≈ 8 %** | ratissage des ~1 237 commits et analyse statique du code historique ; le backlog continue de croître |
| **Vanilla / premier lot VFIX-001 à 005** | **75 %** | patches minimaux préparés et validés statiquement ; test runtime historique restant |
| **Python 3 / wxPython Phoenix** | **88 %** | qualification du portable exact de `master` et validation Windows réelle |
| **UI/UX / thème graphique** | **78 %** | migration/finitions des écrans historiques et validation visuelle réelle |
| **CCNS & extensions** | **83 %** | consolidation de quelques frontières d'architecture et surtout recette métier réelle |

## Pourquoi deux valeurs Vanilla

Le **75 %** ne décrit que le premier lot de cinq correctifs déjà isolés (`VFIX-001` à `VFIX-005`). Il ne doit plus être lu comme « Teamworks Vanilla est corrigé à 75 % ».

L'analyse exhaustive a commencé ensuite et a déjà confirmé de nouvelles familles (`VFIX-006` à `VFIX-009`) ainsi que des pistes de sécurité `VSEC-*`. Tant que ce ratissage n'est pas terminé, le nombre total de corrections à apporter n'est pas connu.

Le seul pourcentage pertinent pour la **complétude de l'inventaire Vanilla** est donc actuellement l'avancement du ratissage historique, soit environ **8 %** du volume de commits, complété par une analyse statique du source original.

## Lecture correcte des pourcentages

- Vanilla / audit exhaustif mesure la **complétude de notre recherche des défauts historiques** ;
- Vanilla / premier lot mesure la **réalisation technique des cinq premiers backports déjà confirmés** ;
- Python 3/Phoenix mesure la migration technique ;
- UI/UX mesure la modernisation visuelle et ergonomique ;
- CCNS mesure le développement fonctionnel ajouté par le fork.

Ces valeurs ne doivent pas être moyennées simplement.

## Avancement global Teamworks-CCNS moderne

Le chantier Vanilla reste un axe parallèle destiné à disposer d'une version historique corrigée ; il **n'entre pas dans le calcul d'avancement du produit Teamworks-CCNS moderne**.

Pondération de lecture conservée :

- Python 3 / Phoenix : **25 %** ;
- UI/UX : **30 %** ;
- CCNS & extensions : **45 %**.

`(88 × 0,25) + (78 × 0,30) + (83 × 0,45) = 82,75`

**Avancement de développement Teamworks-CCNS moderne : environ 83 %.**

Ce 83 % ne vaut pas qualification bêta/RC. Le projet reste en `0.9.0-dev` tant que le portable du SHA exact de `master` n'a pas été construit, parcouru sur Windows et testé sur une copie réelle de la base.

## État du chantier Vanilla

La branche **`vanilla-bugfix`** part directement de :

`00bd52ef85853eb617361a15c2f0cc0cfa1b898e` — Teamworks 2.1.3.1.

Les backports du premier lot sont conservés dans `patches/vanilla/` et validés statiquement sur une copie exacte du snapshot historique.

Le ratissage exhaustif a déjà porté le backlog fonctionnel confirmé de **5 à 9 familles VFIX**. Des faiblesses de sécurité sont suivies séparément sous `VSEC-*` afin de ne pas confondre bugs fonctionnels et durcissement.

## Fichiers détaillés

- `docs/01_VANILLA_BUGFIX.md`
- `docs/02_PYTHON3_PHOENIX.md`
- `docs/03_UI_UX_MODERNISATION.md`
- `docs/04_CCNS_EXTENSIONS.md`
- `patches/vanilla/README.md`

Les pourcentages sont recalculés uniquement lorsque l'état d'un jalon change réellement. Un commit, une CI verte ou une impression de progression ne suffisent pas à eux seuls à faire monter un axe.
