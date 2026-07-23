# TW-059 — Export consolidé du contrôle salarial

L'export consolidé regroupe dans un même rapport les résultats déjà produits par le contrôle salarial : snapshot courant, snapshot précédent optionnel, comparaison, suivi des anomalies et alertes. Il ne crée aucune règle métier et ne recalcule aucun minimum salarial.

## Contenu

Le rapport contient :

- les informations générales : identifiant du rapport, date de génération, référence, version et utilisateur disponible ;
- le résumé du snapshot courant : nombre de contrats, conformes, non conformes, non évalués et écart global ;
- les statistiques de disponibilité des blocs consolidés ;
- le détail complet des contrats du snapshot courant et, si fourni, du snapshot précédent ;
- la comparaison : nouveaux contrats, contrats supprimés, devenus conformes, devenus non conformes et évolution des écarts ;
- le suivi des anomalies : nouvelles, persistantes, résolues et inconnues ;
- les alertes : critiques, avertissements et informations.

## Formats

Deux formats sont disponibles :

- JSON UTF-8, stable et structuré, adapté à l'archivage et à une reprise par un outil comptable ;
- CSV UTF-8 séparé par point-virgule, adapté à une consultation tableur. Le CSV contient d'abord les lignes de synthèse puis le détail des contrats.

Les montants `Decimal` sont sérialisés en chaînes décimales afin d'éviter toute conversion flottante.

## Limites

Sans snapshot précédent, les blocs comparaison, anomalies et alertes sont absents. L'export reflète uniquement les données historisées disponibles dans les snapshots et les services purs existants.

## Usages

La direction ou la comptabilité peut conserver le fichier produit comme état complet d'un contrôle salarial à une date donnée, avec la traçabilité des évolutions lorsqu'un snapshot précédent est sélectionné.
