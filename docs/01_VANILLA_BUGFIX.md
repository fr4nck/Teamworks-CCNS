# Teamworks Vanilla — suivi des bugs et correctifs

## Objectif

Ce fichier recense uniquement les anomalies qui existent dans la version originale de Teamworks (`Noethys/Teamworks`) et que nous rencontrons ou identifions pendant le développement de Teamworks-CCNS.

Objectifs : disposer d'un **Teamworks Vanilla corrigé et utilisable** pendant le développement de Teamworks-CCNS, et identifier les correctifs propres pouvant être proposés au projet d'origine.

## Règle de périmètre

Un élément n'entre ici que si le défaut est vérifiable dans Teamworks Vanilla.

Sont exclus : migration Python 3 / wxPython Phoenix, modernisation UI/UX, CCNS/PMSL et régressions propres à notre fork.

## Référence amont

- Projet original : `Noethys/Teamworks`
- Base commune : `00bd52ef85853eb617361a15c2f0cc0cfa1b898e`
- Fork de développement : `fr4nck/Teamworks-CCNS`

## Inventaire

| ID | Zone | Anomalie | Statut | Preuve / correctif | Test | Upstreamable |
|---|---|---|---|---|---|---|
| VAN-001 | wx / dialogues | Parentage `StaticBox` / contrôles | À auditer | Commits candidats : `8f60b70`, `c10dddd`, `e2bf297`, `9a15534`, `3ddb6a8`, `6885527`, `c240179`, `dab7fef` | Smokes Windows présents côté fork | À déterminer : forte dépendance possible à Phoenix |
| VAN-002 | UI / sizers | Problèmes de sizers/layout de dialogues | À auditer | Candidats : `4914e6f`, `d2c6544`, `3269a49` | Tests/smokes présents côté fork | À déterminer |
| VAN-003 | Personnes / dates | Parsing des dates du dialogue personne | À auditer | Candidat : `416d98b` | Smoke personne présent côté fork | À déterminer |
| VAN-004 | Sauvegardes | `os.listdir(rep)` plante lorsqu'une source de sauvegarde configurée n'existe pas | **Confirmé Vanilla — correctif identifié** | Le code amont appelle directement `os.listdir(rep)` ; correctif minimal déjà identifié dans `2709355` : tester `os.path.isdir(rep)` avant lecture | Couverture restauration/sauvegarde ajoutée côté fork (`53caf1c`, `b317247`) ; test Vanilla à préparer | **Oui, bon candidat** |
| VAN-005 | Gadgets | Actions exécutées sans sélection | À auditer | Candidat : `6bd223c` ; smoke `1790fe2` | Oui côté fork | À déterminer |
| VAN-006 | Aperçu e-mail | Navigation non suffisamment sécurisée | À auditer | Candidat : `79cdb0e` | À déterminer | À déterminer |
| VAN-007 | Listes / contrôleurs | Contrôleurs/listes de référentiels recrutement | À auditer | Candidats : `483199f`, `eaab713`, `ac24ae1`, `b4c6508`, `a3ae40b` | Smoke recrutement présent côté fork | À déterminer |
| VAN-008 | Ressources / icônes | Comportement lorsque des icônes sont absentes | À auditer | Candidats : `10e80e0`, `0225b2b` | Garde-fou côté fork | Probablement lié à la modernisation : prudence |

## Premier résultat vérifié

### VAN-004 — source de sauvegarde absente

Le fichier original `teamworks/Dlg/DLG_Config_sauvegarde.py` construit plusieurs chemins de sources puis utilise `os.listdir(rep)` sans vérifier que le répertoire existe. Une source absente peut donc provoquer une exception avant même que Teamworks puisse simplement considérer cette source comme vide.

Le correctif réalisé dans Teamworks-CCNS (`270935523811459fcf26bf5242af697a363b0270`) est conceptuellement indépendant de Python 3/Phoenix :

- lors de l'affichage, considérer un répertoire absent comme une liste vide ;
- lors de la collecte des fichiers, ignorer les répertoires absents.

Ce correctif est le **premier candidat Vanilla confirmé** de l'inventaire. Il devra être reproduit sur une branche strictement issue de l'original avant intégration au futur fork de maintenance.

## Progression

État de l'inventaire initial :

- candidats recensés : **8 familles** ;
- familles auditées contre l'amont : **1 / 8 (12,5 %)** ;
- bugs Vanilla confirmés : **1** ;
- correctifs Vanilla identifiés : **1** ;
- patches prêts à proposer upstream : **0** (validation sur socle Vanilla encore nécessaire).

> Ce pourcentage mesure l'avancement de l'**audit initial**, pas le taux de bugs corrigés du logiciel.

## Principe pour le futur fork Vanilla corrigé

**Teamworks original + corrections de bugs uniquement.**

Pas de migration Python 3, pas de nouveau thème, pas de CCNS et pas de fonctionnalités supplémentaires.

Toute correction issue de Teamworks-CCNS doit être reconstruite ou isolée sous forme de patch minimal compatible avec le socle Vanilla avant d'y entrer.

## Prochaine étape

Poursuivre l'audit de `VAN-001` à `VAN-003`, puis `VAN-005` à `VAN-008`, en comparant systématiquement le commit correctif au code original. Les correctifs dépendant uniquement de Phoenix ou de notre UI moderne seront retirés du backlog Vanilla.
