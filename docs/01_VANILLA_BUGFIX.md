# Teamworks Vanilla — suivi des bugs et correctifs

## Objectif

Ce fichier recense uniquement les anomalies qui existent dans la version originale de Teamworks (`Noethys/Teamworks`) et que nous rencontrons ou identifions pendant le développement de Teamworks-CCNS.

Le but est double :

1. disposer à terme d'un **Teamworks Vanilla corrigé et utilisable**, sans lui ajouter les évolutions de Teamworks-CCNS ;
2. identifier les correctifs suffisamment génériques et propres pour pouvoir être proposés au projet d'origine.

## Règle de périmètre

Un élément n'entre dans cette liste que si le défaut est reproductible ou vérifiable dans Teamworks Vanilla.

Ce fichier **n'inclut pas** :

- les problèmes créés par la migration Python 3 / wxPython Phoenix ;
- la modernisation graphique et UI/UX ;
- les fonctionnalités CCNS ;
- les fonctionnalités propres à PMSL ;
- les régressions introduites uniquement dans notre fork.

Ces éléments sont suivis séparément.

## Référence amont

- Projet original : `Noethys/Teamworks`
- Base commune identifiée : `00bd52ef85853eb617361a15c2f0cc0cfa1b898e`
- Fork de développement : `fr4nck/Teamworks-CCNS`

## Statuts

- `À vérifier` : anomalie rencontrée chez nous, présence dans Vanilla à confirmer.
- `Confirmé Vanilla` : défaut vérifié dans le code/version d'origine.
- `Correctif identifié` : cause comprise et correction minimale connue.
- `Corrigé Vanilla` : correctif compatible avec le socle original préparé/appliqué.
- `Testé` : correction validée sans dépendre de Teamworks-CCNS.
- `Upstreamable` : patch suffisamment isolé pour être proposé au projet d'origine.

## Inventaire

| ID | Zone | Anomalie | Statut | Reproduit Vanilla | Correctif Vanilla | Test | Upstreamable | Notes |
|---|---|---|---|---|---|---|---|---|
| VAN-001 | wx / dialogues | Parentage `StaticBox` / contrôles : plusieurs corrections rencontrées pendant le débogage | À vérifier | À auditer | À isoler | Certains tests existent côté fork | À déterminer | Distinguer défaut historique et adaptations Phoenix |
| VAN-002 | UI / sizers | Problèmes de sizers/layout rencontrés dans plusieurs dialogues | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Ne pas inclure les problèmes provenant du nouveau thème |
| VAN-003 | Personnes / dates | Parsing et gestion de dates ayant nécessité des corrections | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Comparer strictement au comportement original |
| VAN-004 | Sauvegardes | Robustesse face aux sources/fichiers de sauvegarde absents | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Bon candidat si le défaut est confirmé en Vanilla |
| VAN-005 | Gadgets | Gestion de cas sans sélection / état incomplet | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Exclure les gadgets ajoutés par CCNS |
| VAN-006 | Aperçu e-mail | Sécurisation de la navigation dans l'aperçu e-mail | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Vérifier le code amont avant classement définitif |
| VAN-007 | Listes / contrôleurs | Défauts génériques rencontrés dans certains contrôleurs et listes | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Inventorier les commits concernés avant validation |
| VAN-008 | Ressources / icônes | Comportement en présence d'icônes ou ressources absentes | À vérifier | À auditer | À isoler | À déterminer | À déterminer | Ne conserver que les cas présents dans l'original |

## Progression

La progression de ce chantier ne sera calculée qu'après le premier audit complet des anomalies candidates. Un pourcentage avant cette étape serait artificiel.

Les éléments `À vérifier` ne comptent pas comme bugs Vanilla confirmés.

### Indicateurs à calculer après audit

- nombre de bugs Vanilla confirmés ;
- nombre de correctifs Vanilla réalisés ;
- nombre de correctifs testés ;
- nombre de patches upstreamables ;
- pourcentage de traitement du backlog Vanilla confirmé.

## Principe pour le futur fork Vanilla corrigé

Le futur fork de maintenance doit rester aussi proche que possible de Teamworks original :

**Teamworks original + corrections de bugs uniquement.**

Pas de migration Python 3, pas de nouveau thème, pas de CCNS et pas de fonctionnalités supplémentaires.

Toute correction issue de Teamworks-CCNS doit donc être reconstruite ou isolée sous forme de patch minimal compatible avec le socle Vanilla avant d'y entrer.

## Prochaine étape

Auditer les candidats `VAN-001` à `VAN-008` contre `Noethys/Teamworks`, retrouver les commits correspondants dans `Teamworks-CCNS`, puis reclasser chaque élément en :

- bug Vanilla confirmé ;
- régression de migration ;
- problème UI/UX moderne ;
- extension CCNS/PMSL.

Le pourcentage d'avancement Vanilla sera calculé à partir de cet inventaire assaini.
