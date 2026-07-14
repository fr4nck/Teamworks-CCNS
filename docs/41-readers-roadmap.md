# Feuille de route des Readers de données

Cette note prépare l'extraction progressive des lectures SQL encore dispersées dans les écrans wxPython. Elle ne change pas les règles métier : les Readers proposés restent des lecteurs fins au-dessus de `GestionDB`, testables sans interface graphique, et réutilisables ensuite par des services métier.

## Constats issus du dépôt

Un balayage des requêtes Python montre les zones les plus sollicitées suivantes :

| Domaine | Fréquence observée | Duplication | Extraction | Intérêt architectural |
| --- | ---: | --- | --- | --- |
| Contrats | très élevée, environ 70 occurrences autour de `contrats`, `contrats_class`, `contrats_types`, modèles et champs | forte mais avec variantes métier nombreuses | moyenne | très fort : moteur CCNS, publipostage, création et listes |
| Personnes | élevée, environ 40 occurrences | forte pour l'identité minimale `IDpersonne, nom, prenom` | facile | fort : listes, frais, impressions, présences, scénarios |
| Paramètres | moyenne, environ 20 occurrences autour de `parametres`, `divers`, `gadgets` | forte sur certains couples catégorie/nom et gadgets | facile à moyenne | fort pour la testabilité, mais sensible aux effets de bord de configuration |
| Activités / présences | moyenne à élevée selon les écrans, souvent via `presences`, catégories et planning | moyenne | moyenne | fort pour les écrans volumineux et la performance perçue |
| Inscriptions | faible dans le balayage direct, souvent masquée par des contrôles génériques | faible à moyenne | moyenne | utile après clarification des usages métier |
| Utilisateurs | faible | faible | facile | intérêt ponctuel sécurité/procédures |
| Structures | non significatif dans les noms de tables détectés | à confirmer | à confirmer | à traiter après cartographie du schéma réel |
| Salariés / individus | faible en accès direct, mais présent via contrats et audit CCNS | faible en nom de table, fort conceptuellement | moyenne | à rattacher au Reader contrats ou personnes selon les usages |

## Extraction retenue dans cette étape

Le premier Reader dédié est `PersonReader`, limité à la lecture des identités minimales des personnes :

```sql
SELECT IDpersonne, nom, prenom FROM personnes ORDER BY nom, prenom;
```

Ce choix est volontairement peu risqué : la requête est identique dans plusieurs écrans, ne porte pas de règle métier, ne modifie pas le tri historique et se prête à des tests unitaires sans wxPython. Les premiers appels migrés concernent les frais, l'impression de photos et la saisie de déplacements. Les écrans conservent leurs transformations locales de libellés afin de ne pas modifier l'interface utilisateur.

## Ordre recommandé des prochains Readers

1. **PersonReader** : compléter les migrations des listes de sélection simples, puis ajouter si nécessaire une lecture par identifiant pour remplacer les requêtes `nom, prenom` isolées.
2. **ContractReader** : extraire les lectures de contrats, classifications, types, champs personnalisés et modèles. Ce Reader devra rester aligné avec `CcnsDataReader` pour éviter deux cartographies concurrentes du périmètre CCNS.
3. **SettingsReader** : centraliser les lectures `parametres`, `divers` et `gadgets`, en séparant les paramètres applicatifs des préférences d'écran.
4. **PresenceActivityReader** : regrouper présences, catégories, jours fériés et périodes utiles au planning et aux impressions.
5. **RegistrationReader** : isoler les inscriptions après inventaire des usages réels dans les contrôles génériques.
6. **UserReader** : couvrir les lectures de comptes utilisées par les procédures et la configuration réseau.
7. **StructureReader** : à créer seulement après confirmation des tables et des écrans concernés dans le schéma de production.

## Dépendances et simplifications attendues

- `ContractReader` dépendra fonctionnellement de l'identité personne pour les libellés salarié, mais ne doit pas appeler wxPython. La composition devra se faire dans un service métier ou un DTO de lecture.
- `SettingsReader` pourra simplifier les dialogues de paramètres, l'accueil et les utilitaires de préférences en supprimant les requêtes répétées par nom de gadget ou par couple catégorie/nom.
- `PresenceActivityReader` pourra préparer des optimisations mesurées des écrans planning et impressions en séparant temps SQL, transformation Python et rendu wxPython.
- Les modules les plus susceptibles d'être simplifiés ensuite sont les dialogues de sélection/impression, `teamworks/Ol/OL_personnes.py`, `teamworks/Ol/OL_contrats.py`, les contrôles de création de contrat et les utilitaires de publipostage.

Les gains attendus sont d'abord architecturaux : moins de SQL dispersé, tests unitaires plus ciblés, point unique pour mesurer les lectures et migration progressive vers des services métier. Les gains de performance devront rester mesurés avant/après avec l'instrumentation existante ; aucun cache global n'est recommandé à ce stade.
