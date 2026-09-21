# Qt Vanilla 0.1 — seuils de performance MySQL

Ces seuils sont des **critères de sortie de la Qt Vanilla 0.1**. Ils ne prétendent pas définir la performance idéale du produit à long terme.

Ils s'appliquent au même SHA, sur :

- le poste Windows réel de recette ;
- la version MySQL réellement déployée ;
- une copie anonymisée de volumétrie proche de l'exploitation ;
- le même réseau que l'usage réel lorsque cela est possible.

## 1. Méthode de mesure

Pour chaque parcours P-01 à P-11 :

1. effectuer un premier passage de chauffe non comptabilisé ;
2. effectuer **10 mesures** ;
3. conserver chaque valeur brute ;
4. calculer médiane (p50) et p95 ;
5. noter toute valeur aberrante et son contexte ;
6. mesurer la wx sur le même poste/base lorsque le parcours équivalent existe.

Aucune mesure ne doit être prise pendant :

- une sauvegarde serveur ;
- une mise à jour Windows ;
- un antivirus en scan complet identifié ;
- un autre traitement lourd connu sur la même base.

Si un tel événement survient, la série est annulée et recommencée.

## 2. Seuils absolus

| ID | Parcours | p50 cible | p95 maximum | Verdict |
|---|---|---:|---:|---|
| P-01 | démarrage à chaud → fenêtre utilisable | ≤ 3,0 s | ≤ 5,0 s | Bloquant si dépassé de façon reproductible |
| P-02 | liste Individus | ≤ 1,5 s | ≤ 3,0 s | Bloquant |
| P-03 | recherche individu | ≤ 0,5 s | ≤ 1,0 s | Bloquant |
| P-04 | changement individu → Généralités stables | ≤ 1,0 s | ≤ 2,0 s | Bloquant |
| P-05 | chargement Contrats | ≤ 1,0 s | ≤ 2,0 s | Bloquant |
| P-06 | chargement Présences | ≤ 1,5 s | ≤ 3,0 s | Bloquant |
| P-07 | chargement Scénarios | ≤ 1,5 s | ≤ 3,0 s | Bloquant |
| P-08 | chargement Frais | ≤ 1,5 s | ≤ 3,0 s | Bloquant |
| P-09 | écriture Contrat + commit + relecture | ≤ 2,0 s | ≤ 3,5 s | Bloquant |
| P-10 | écriture Remboursement + relations + relecture | ≤ 2,0 s | ≤ 3,5 s | Bloquant |
| P-11 | Documents RH → modèles/état affichés | ≤ 1,5 s | ≤ 3,0 s | Bloquant |

### Démarrage à froid

Le premier lancement après redémarrage Windows ou purge des caches peut dépasser le seuil P-01.

Pour la 0.1 :

- cible : ≤ 5 s ;
- maximum acceptable : ≤ 8 s ;
- > 8 s reproductible : **FAIL performance**.

Le démarrage à froid est consigné séparément du démarrage à chaud.

## 3. Régression relative par rapport à la wx

Lorsque le même parcours existe dans la wx et produit une information comparable :

```text
ratio = p50_Qt / p50_wx
```

Classification :

| Ratio Qt / wx | Décision |
|---:|---|
| ≤ 1,20 | PASS |
| > 1,20 et ≤ 1,50 | À analyser ; acceptable uniquement si le seuil absolu reste vert et si la cause est documentée |
| > 1,50 | FAIL sauf décision explicite avant release |

La comparaison wx ne remplace jamais les seuils absolus : une wx très lente n'autorise pas une Qt très lente.

## 4. Réactivité UI

Même lorsqu'un chargement métier dure plus longtemps, la fenêtre Qt doit rester réactive.

| Contrôle | Seuil |
|---|---|
| réaction visible à un clic | < 200 ms |
| changement d'état d'un bouton/selection | < 200 ms |
| apparition d'un indicateur de chargement si opération longue | < 300 ms |
| gel complet de la fenêtre | interdit au-delà de 500 ms hors ouverture native de dialogue |

Un traitement de plus de 2 s qui bloque totalement l'event loop est un **FAIL**, même si le temps total respecte le tableau précédent.

## 5. Endurance P-12

Séquence :

1. sélectionner 50 individus successivement ;
2. alterner dossiers simples et lourds ;
3. ouvrir Contrats/Frais/Documents sur plusieurs d'entre eux ;
4. revenir aux 10 premiers.

Mesures :

- p50 des 10 premiers changements ;
- p50 des 10 derniers ;
- pire temps observé.

PASS si :

```text
p50_derniers <= p50_premiers * 1,20
```

et :

- aucun temps individuel > 5 s sans raison externe identifiée ;
- aucune erreur de thread ;
- aucune donnée d'un individu précédent affichée sur le suivant.

Une dérive > 20 % est à analyser.

Une dérive > 50 % est **FAIL**.

## 6. Connexions MySQL P-13

Avant lancement :

```sql
SHOW PROCESSLIST;
```

Relever le nombre de connexions Teamworks.

Pendant la navigation :

- le nombre peut augmenter pour les readers/adaptateurs prévus ;
- il doit atteindre un plateau ;
- il ne doit pas croître à chaque changement d'individu ou ouverture de dialogue.

Après fermeture de Qt :

- retour au niveau initial dans les 10 secondes ;
- aucune connexion Teamworks durablement bloquée.

### Verdict

- croissance monotone au fil des clics : **FAIL** ;
- connexion encore active > 30 s après fermeture sans raison serveur : **FAIL** ;
- aucune accumulation : PASS.

## 7. Mémoire P-14

Mesurer le RSS du processus Qt :

1. après stabilisation de la fenêtre initiale ;
2. après 10 changements d'individu ;
3. après 50 changements ;
4. après ouverture répétée de Contrats, Frais et Documents.

Classification :

| Croissance RSS après endurance | Décision |
|---:|---|
| ≤ 20 % et ≤ 100 MiB | PASS |
| > 20 % ou > 100 MiB | Analyse obligatoire |
| > 50 % ou > 250 MiB avec croissance non stabilisée | FAIL |

La mémoire peut rester supérieure au point de départ à cause des caches Qt/Python ; ce qui est interdit est une **croissance continue non stabilisée**.

## 8. Requêtes lentes

Si un parcours dépasse son seuil :

1. identifier l'opération ;
2. mesurer le temps côté client ;
3. regarder le temps côté MySQL ;
4. utiliser `EXPLAIN` sur les SELECT responsables ;
5. vérifier index, cardinalité et nombre de requêtes.

Pour chaque requête responsable de plus de 500 ms de façon répétée, le PV doit conserver :

- requête ou identifiant du service concerné ;
- durée ;
- `EXPLAIN` ;
- nombre de lignes examinées ;
- décision : correction / acceptation motivée.

Ne pas activer un slow-query log global sur le serveur de production pour cette recette sans validation d'exploitation. Sur un serveur de recette identique, il peut être utilisé si nécessaire.

## 9. Volumétrie minimale pour qualifier la performance

La petite sélection fonctionnelle de 50–100 individus ne suffit pas.

La copie utilisée pour P-* doit conserver au moins :

- **80 % du nombre réel d'individus**, ou toute la base anonymisée ;
- **80 % des contrats** ;
- **80 % des présences** ;
- **80 % des déplacements/remboursements** ;
- la distribution réelle des personnes sans/avec plusieurs contrats.

Si l'on ne peut pas atteindre cette volumétrie, le verdict performance doit être marqué **NON QUALIFIÉ**, pas PASS.

## 10. Verdict performance

PASS uniquement si :

- tous les P-01 à P-11 bloquants respectent les seuils ou disposent d'une dérogation explicitement signée avant release ;
- P-12 ne montre pas de dérive > 50 % ;
- P-13 ne montre aucune fuite de connexion ;
- P-14 ne montre aucune croissance mémoire non stabilisée au-delà du seuil bloquant ;
- aucune régression Qt/wx > 50 % n'est laissée sans décision explicite.

Le PV doit conserver les valeurs brutes, pas seulement le verdict.
