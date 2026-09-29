# Registre des versions des règles DPAE

La source machine du registre est `domain/dpae/rules_versions.json`.

Format : `YYYY-MM-DD.N`.

La date identifie l'introduction du jeu de règles dans Teamworks ; elle ne vaut
pas date d'effet réglementaire. Une éventuelle date d'effet est enregistrée
séparément dans `regulatory_effective_from`.

Toute différence entre la `dpae_rules_version` d'une préparation éphémère et la
version courante interdit la transmission de cette préparation et impose sa
reconstruction complète depuis les sources canoniques.

## 2026-09-27.1

| Champ | Valeur |
|---|---|
| `dpae_rules_version` | `2026-09-27.1` |
| Date d'introduction | `2026-09-27` |
| `regulatory_effective_from` | `N/A` |
| Statut | `ACTIVE` |
| PR | `#477` |
| Version fingerprint | `1` |
| Version précédente | `NONE` |
| Invalidation des préparations antérieures | `OUI` |

### Objet

Version initiale du contrat fonctionnel DPAE V1 : résolution des données depuis
les sources Teamworks, validations préalables, comparaison contrat/planning et
empreinte canonique d'une préparation éphémère.

### Règle de changement de version

Une nouvelle version est requise lorsqu'à sources identiques une modification
peut changer le payload DPAE, le verdict d'une validation ou une confirmation
présentée à l'utilisateur avant transmission.

Un refactoring, une optimisation SQL, un index, des logs, des tests ou un
changement de version générale de Teamworks ne créent pas de version lorsque le
comportement DPAE reste identique.
