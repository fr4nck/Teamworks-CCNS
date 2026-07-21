# Diagnostic Dolibarr 23 — accès aux factures

## Constat observé

Diagnostic reçu sur une instance Dolibarr 23.0.3 :

| Contrôle | Résultat |
| --- | --- |
| Module `invoice` détecté | Non |
| Module `supplier_invoice` détecté | Non |
| Droit lecture factures clients | Non |
| Droit lecture factures fournisseurs | Non |

Ce résultat doit être traité comme un blocage fonctionnel pour toute intégration qui lit les factures depuis l'API Dolibarr : l'utilisateur API ne voit ni les services de factures clients, ni les services de factures fournisseurs, ni les droits de lecture associés.

## Interprétation

Pour Dolibarr 23, la présence de la version seule ne suffit pas. Les points suivants doivent être vrais simultanément :

1. le module REST API doit être actif ;
2. le module de factures clients doit être actif pour exposer les routes de factures clients ;
3. le module de factures fournisseurs doit être actif pour exposer les routes de factures fournisseurs ;
4. la clé API doit appartenir à un utilisateur disposant des droits de lecture correspondants ;
5. en contexte multi-société, l'entité transmise à l'API doit être celle qui porte les modules et les droits attendus.

Les routes REST attendues côté Dolibarr sont notamment :

- `GET /api/index.php/invoices` pour les factures clients ;
- `GET /api/index.php/supplierinvoices` pour les factures fournisseurs.

Un diagnostic qui cherche uniquement les libellés techniques `invoice` et `supplier_invoice` peut être trop fragile si l'instance expose les capacités via les routes REST ou via des noms internes différents. Le contrôle doit donc croiser les modules, les droits et la disponibilité effective des routes.

## Procédure de vérification manuelle

1. Se connecter à Dolibarr avec un compte administrateur.
2. Ouvrir la configuration des modules et vérifier que le module REST API est activé.
3. Vérifier que la facturation client est activée.
4. Vérifier que la facturation fournisseur est activée si l'intégration doit lire les factures fournisseurs.
5. Ouvrir la fiche de l'utilisateur porteur de la clé API.
6. Vérifier les permissions de lecture des factures clients et fournisseurs.
7. Ouvrir l'explorateur REST de l'instance avec la même clé API.
8. Confirmer que les routes `invoices` et `supplierinvoices` sont visibles et testables.

## Décision d'intégration

| Situation | Décision recommandée |
| --- | --- |
| Route `invoices` absente | Désactiver la lecture des factures clients et afficher une action de configuration Dolibarr. |
| Route `supplierinvoices` absente | Désactiver la lecture des factures fournisseurs et afficher une action de configuration Dolibarr. |
| Route visible mais réponse 403 | Signaler un problème de droits de l'utilisateur API. |
| Route visible mais réponse 401 | Signaler une clé API absente, invalide ou transmise au mauvais en-tête. |
| Route visible mais liste vide | Considérer l'accès valide ; ne pas confondre absence de données et absence de droits. |

## Message utilisateur conseillé

> Dolibarr 23.0.3 répond, mais l'utilisateur API ne dispose pas d'un accès exploitable aux factures. Activez les modules de facturation nécessaires et accordez les droits de lecture des factures clients et fournisseurs à l'utilisateur qui porte la clé API, puis vérifiez les routes `invoices` et `supplierinvoices` dans l'explorateur REST.

## Référence externe de vérification

La documentation développeur Dolibarr indique que les services REST disponibles dépendent des modules activés, que l'explorateur REST doit être testé avec le jeton de l'utilisateur concerné, et donne l'exemple de l'appel `GET /api/index.php/invoices` pour les factures clients.
