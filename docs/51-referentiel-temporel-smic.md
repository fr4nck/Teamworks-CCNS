# Référentiel temporel du SMIC

Le SMIC est une donnée réglementaire qui évolue dans le temps. Une nouvelle valeur ne remplace donc jamais rétroactivement une ancienne valeur : chaque montant est porté par une version datée, avec des bornes inclusives et une référence réglementaire explicite.

## Territoires couverts

Le référentiel distingue deux périmètres dans ce ticket :

- `METROPOLITAN_FRANCE`, qui couvre la métropole, la Guadeloupe, la Guyane, la Martinique, La Réunion, Saint-Barthélemy, Saint-Martin et Saint-Pierre-et-Miquelon ;
- `MAYOTTE`, qui conserve ses montants propres.

Aucune valeur distincte n'est créée pour chacun des territoires rattachés au périmètre métropolitain dans TW-028.

## Revalorisations 2026 intégrées

Quatre versions sont disponibles pour représenter les deux périodes applicables en 2026 :

| Territoire | Début | Fin | Montant horaire brut | Montant mensuel brut indicatif 35 h | Référence |
| --- | --- | --- | --- | --- | --- |
| Métropole | 1er janvier 2026 | 31 mai 2026 | `Decimal("12.02")` | `Decimal("1823.03")` | Décret n° 2025-1228 du 17 décembre 2025 |
| Mayotte | 1er janvier 2026 | 31 mai 2026 | `Decimal("9.33")` | `Decimal("1415.05")` | Décret n° 2025-1228 du 17 décembre 2025 |
| Métropole | 1er juin 2026 | période ouverte | `Decimal("12.31")` | `Decimal("1867.02")` | Arrêté du 22 mai 2026 |
| Mayotte | 1er juin 2026 | période ouverte | `Decimal("9.56")` | `Decimal("1449.93")` | Arrêté du 22 mai 2026 |

Les périodes de territoires différents peuvent se superposer. Les périodes d'un même territoire ne peuvent pas se chevaucher. Les trous temporels restent autorisés et ne déclenchent aucun repli vers la dernière valeur connue.

## Montants officiels conservés séparément

Le montant horaire brut et le montant mensuel brut indicatif à 35 heures sont conservés comme deux données réglementaires publiées. Le référentiel ne recalcule pas automatiquement le mensuel depuis l'horaire et ne rejette pas une version en raison d'un écart d'arrondi théorique.

Tous les montants et la durée légale de référence utilisent `Decimal`. Les objets sont immuables et les collections de versions sont des tuples.

## Limites volontaires

TW-028 ajoute uniquement le référentiel temporel pur du SMIC. Il ne compare pas encore le SMIC au minimum conventionnel CCNS, ne choisit pas le montant le plus favorable au salarié, ne calcule aucune paie, ne traite pas la proratisation, les apprentis, les mineurs, les abattements, les avantages en nature, le minimum garanti ou les alertes réglementaires.

Aucune persistance, interface graphique, API, récupération Internet, consultation de la date courante ou modification automatique de contrat n'est ajoutée.
