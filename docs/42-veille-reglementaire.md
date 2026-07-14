# Socle de veille réglementaire CCNS

Ce socle prépare une veille autonome des références réglementaires et salariales sans modifier automatiquement les règles métier, les grilles datées ni les données de production.

## Périmètre initial

Les familles suivies sont modélisées pour couvrir progressivement :

- la Convention collective nationale du sport — IDCC 2511 ;
- les avenants relatifs aux salaires minimums conventionnels ;
- les modifications générales de la CCNS ;
- le montant officiel du SMIC ;
- la règle et le minimum applicables aux contrats d'engagement éducatif ;
- les arrêtés d'extension et leurs dates d'entrée en vigueur.

## Chaîne de sécurité

Le fonctionnement attendu reste volontairement conservateur :

```text
Détection
    ↓
Enregistrement de la source
    ↓
Comparaison avec la dernière version connue
    ↓
Alerte ou proposition
    ↓
Validation humaine
    ↓
Application éventuelle dans une PR ultérieure
```

Le code ajouté s'arrête à la détection, l'enregistrement d'instantanés et la production d'un résultat indiquant si une validation humaine est nécessaire.

## Architecture

- `domain/regulatory/watch.py` contient les entités de référence, d'instantané et de changement détecté.
- `application/services/ccns/regulatory_watch.py` orchestre la récupération d'une source, la comparaison et l'enregistrement du nouvel instantané.
- `infrastructure/regulatory_watch/json_snapshot_store.py` fournit un stockage JSON append-only minimal pour conserver l'historique des sources observées.

Aucune classe de ce socle ne met à jour les grilles salariales, le moteur CCNS ou la base métier. Une PR ultérieure pourra ajouter des collecteurs concrets pour les sources officielles et une interface de validation humaine.
