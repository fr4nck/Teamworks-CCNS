# Sources réglementaires officielles pour la veille CCNS

## Objectif et périmètre

Ce document qualifie les sources officielles à utiliser pour raccorder le socle de veille réglementaire CCNS aux données publiques, sans appliquer automatiquement les règles métier. La priorité est donnée aux API documentées, aux jeux de données ouverts et aux flux structurés. Les consultations HTML et PDF restent des solutions de dernier recours ou des supports de validation humaine.

## Synthèse des choix

| Domaine | Source recommandée | Usage cible | Priorité d'intégration |
| --- | --- | --- | --- |
| CCNS IDCC 2511, avenants, textes attachés, arrêtés d'extension | API Légifrance stable via PISTE | Recherche et consultation des fonds `KALI` et `JORF` | 1 |
| Métadonnées et disponibilité de l'API Légifrance | Fiche data.gouv du service API Légifrance | Vérifier l'existence, la licence, les conditions et documenter la dépendance | Prototype uniquement |
| SMIC | API Légifrance stable via PISTE sur les textes JORF + page INSEE en contrôle documentaire | Détecter les décrets/arrêtés publiés au JO et historiser les dates d'effet | 2 |
| Contrat d'engagement éducatif | API Légifrance stable via PISTE sur le Code de l'action sociale et des familles et les textes JORF | Surveiller les articles `L432-*`, `D432-*` et leurs textes modificateurs | 3 |
| Information vulgarisée | Service-public.fr / Code du travail numérique / ministère du Travail | Aide à la validation humaine, non source primaire d'automatisation | Non prioritaire |

## Source retenue n°1 : API Légifrance stable via PISTE

- **Organisme producteur** : Direction de l'information légale et administrative (DILA), sous responsabilité éditoriale du Secrétariat général du Gouvernement.
- **URL officielle** : <https://www.legifrance.gouv.fr/contenu/pied-de-page/open-data-et-api> ; fiche data.gouv : <https://www.data.gouv.fr/dataservices/legifrance> ; portail PISTE : <https://piste.gouv.fr/>.
- **API disponible** : oui, API stable ouverte le 4 avril 2023. La version bêta est fermée depuis le 6 juin 2023.
- **Format disponible** : JSON via API ; documentation Swagger sur PISTE ; documentation complémentaire pour les fonds, tris et filtres.
- **Stabilité estimée** : élevée. Source primaire officielle, version stable, maintenance annoncée sur la page Légifrance.
- **Authentification** : oui. Compte PISTE, application déclarée, OAuth2 client credentials.
- **Fréquence de mise à jour** : alignée sur Légifrance et le Journal officiel ; à interroger quotidiennement pour la veille.
- **Licence d'utilisation** : licence ouverte 2.0, avec conditions générales PISTE et conditions de l'API Légifrance.
- **Limites de débit** : quotas indiqués dans le portail PISTE ; à mesurer après obtention des clés.
- **Facilité d'intégration** : moyenne. L'authentification et les requêtes de recherche sont plus complexes qu'un téléchargement statique, mais l'API évite le scraping et fournit les fonds pertinents.
- **Qualité documentaire** : bonne côté portail PISTE et FAQ Légifrance ; accès complet à la documentation technique soumis à inscription.
- **API préférable au téléchargement** : oui pour Teamworks-CCNS. Elle permet des recherches ciblées par fonds, identifiant, mots-clés, dates et versions, ce qui évite de charger l'ensemble des bases juridiques.
- **Clé nécessaire** : oui.

### Usages CCNS recommandés

Pour la convention collective nationale du sport :

- utiliser le fonds `KALI` pour les conventions collectives, les avenants et textes attachés ;
- suivre la convention IDCC 2511, son identifiant Légifrance public et les résultats de recherche rattachés au sport ;
- surveiller les arrêtés d'extension dans le fonds `JORF`, car l'opposabilité des avenants dépend de leur publication et de leur date d'effet ;
- stocker uniquement des instantanés techniques et imposer une validation humaine avant toute modification des grilles.

Pour le SMIC :

- surveiller les textes JORF portant relèvement du salaire minimum de croissance ;
- extraire, après validation humaine, le montant horaire brut, la date de publication et la date d'application ;
- utiliser l'INSEE ou le ministère du Travail comme contrôle documentaire secondaire, pas comme source unique d'automatisation si aucun flux structuré historisé n'est garanti.

Pour le contrat d'engagement éducatif :

- surveiller le Code de l'action sociale et des familles, notamment les articles `L432-1` à `L432-6` et `D432-1` à `D432-9` ;
- suivre les textes modificateurs JORF, par exemple les décrets qui modifient l'article `D432-2` sur la rémunération minimale exprimée en multiple du SMIC horaire ;
- conserver le lien avec le SMIC comme dépendance réglementaire explicite, sans recalcul automatique non validé.

## Source retenue n°2 : API data.gouv des métadonnées de services

- **Organisme producteur** : data.gouv.fr / Etalab, avec fiche publiée pour l'API Légifrance.
- **URL officielle** : <https://www.data.gouv.fr/dataservices/legifrance> ; accès JSON utilisé par le prototype : <https://www.data.gouv.fr/api/1/dataservices/legifrance/>.
- **API disponible** : oui, API publique data.gouv.
- **Format disponible** : JSON pour les métadonnées, HTML pour la fiche.
- **Stabilité estimée** : élevée pour la métadonnée de catalogue, insuffisante comme source juridique métier.
- **Authentification** : non pour la lecture publique de la fiche.
- **Fréquence de mise à jour** : selon la mise à jour de la fiche data.gouv, pas selon chaque changement juridique.
- **Licence d'utilisation** : la fiche renvoie à la licence ouverte 2.0 et aux conditions Légifrance/PISTE.
- **Limites de débit** : non bloquantes pour un usage ponctuel ; à traiter avec politesse réseau et cache.
- **Facilité d'intégration** : élevée.
- **Qualité documentaire** : bonne pour identifier la source, mauvaise pour détecter les évolutions réglementaires.
- **API préférable au téléchargement** : oui uniquement pour surveiller les métadonnées de dépendance.
- **Clé nécessaire** : non.

Cette source a été choisie pour le prototype minimal, car elle est officielle, structurée, sans authentification et permet de valider le raccord technique `source JSON -> RegulatorySnapshot` sans exposer de secret PISTE ni modifier le métier.

## Source retenue n°3 : Journal officiel API / flux structurés

- **Organisme producteur** : DILA.
- **URL officielle** : <https://www.journal-officiel.gouv.fr/api-console/explore/v2.1/>.
- **API disponible** : oui, API JSON de consultation du Journal officiel.
- **Format disponible** : JSON.
- **Stabilité estimée** : moyenne à élevée, mais le périmètre doit être vérifié face à l'API Légifrance qui couvre aussi le JORF.
- **Authentification** : à vérifier selon les endpoints utilisés ; la console indique des endpoints GET JSON.
- **Fréquence de mise à jour** : quotidienne, selon publication du JO.
- **Licence d'utilisation** : données publiques DILA, à confirmer endpoint par endpoint.
- **Limites de débit** : à vérifier dans la documentation de l'API.
- **Facilité d'intégration** : moyenne.
- **Qualité documentaire** : correcte pour explorer les publications, moins adaptée que Légifrance pour relier versions consolidées, codes et conventions.
- **API préférable au téléchargement** : oui pour détecter rapidement les publications du jour ; Légifrance reste préférable pour la consolidation juridique.
- **Clé nécessaire** : à vérifier avant intégration.

Cette source peut compléter Légifrance pour une alerte quotidienne de publication, mais ne doit pas remplacer la consultation consolidée des textes.

## Source retenue n°4 : INSEE pour le SMIC en contrôle documentaire

- **Organisme producteur** : INSEE.
- **URL officielle** : <https://www.insee.fr/fr/statistiques/1375188>.
- **API disponible** : non identifiée comme source directe simple et stable pour le montant horaire courant du SMIC dans le cadre de cette étude.
- **Format disponible** : page statistique HTML, tableaux téléchargeables selon les pages INSEE.
- **Stabilité estimée** : élevée comme source statistique, moyenne pour une intégration automatisée sans flux dédié.
- **Authentification** : non pour la page publique.
- **Fréquence de mise à jour** : à chaque publication statistique ou changement repris par l'INSEE.
- **Licence d'utilisation** : données publiques INSEE, conditions de réutilisation à respecter.
- **Limites de débit** : non pertinent pour une consultation documentaire ; ne pas scraper.
- **Facilité d'intégration** : faible à moyenne si aucun flux structuré stable n'est retenu.
- **Qualité documentaire** : bonne, avec montants, dates d'entrée en vigueur et distinction France hors Mayotte/Mayotte.
- **API préférable au téléchargement** : une API serait préférable, mais non retenue sans endpoint clair pour cette donnée précise.
- **Clé nécessaire** : non pour la consultation publique.

Recommandation : utiliser l'INSEE comme source secondaire de validation humaine des montants, et l'API Légifrance/JORF comme source primaire de détection.

## Source retenue n°5 : Code du travail numérique

- **Organisme producteur** : ministère du Travail.
- **URL officielle** : <https://code.travail.gouv.fr/convention-collective/2511-sport>.
- **API disponible** : non retenue pour cette PR ; l'existence d'API internes ou publiques doit être vérifiée avant toute automatisation.
- **Format disponible** : HTML public.
- **Stabilité estimée** : bonne pour la consultation, insuffisante pour une automatisation sans API documentée.
- **Authentification** : non.
- **Fréquence de mise à jour** : selon mise à jour éditoriale du service.
- **Licence d'utilisation** : service public ; vérifier les conditions avant réutilisation automatisée.
- **Limites de débit** : non documentées pour un usage de veille automatisée.
- **Facilité d'intégration** : faible si l'on exclut le scraping HTML.
- **Qualité documentaire** : très bonne pour l'orientation utilisateur et les thèmes conventionnels.
- **API préférable au téléchargement** : oui, mais non identifiée comme source primaire.
- **Clé nécessaire** : non pour la page HTML.

Recommandation : ne pas l'utiliser comme source automatique principale. S'en servir comme aide de validation humaine et de navigation vers Légifrance.

## Source retenue n°6 : Service-public.fr pour le contrat d'engagement éducatif

- **Organisme producteur** : Direction de l'information légale et administrative.
- **URL officielle** : <https://www.service-public.gouv.fr/particuliers/vosdroits/F23425>.
- **API disponible** : non retenue pour la veille technique CCNS.
- **Format disponible** : HTML éditorial.
- **Stabilité estimée** : élevée côté service public, mais contenu vulgarisé et non source normative primaire.
- **Authentification** : non.
- **Fréquence de mise à jour** : selon mise à jour éditoriale.
- **Licence d'utilisation** : conditions service-public.fr à vérifier avant réutilisation massive.
- **Limites de débit** : non adaptées à une collecte automatisée.
- **Facilité d'intégration** : faible sans scraping.
- **Qualité documentaire** : bonne pour l'explication métier.
- **API préférable au téléchargement** : oui, mais source primaire non nécessaire si Légifrance couvre les textes.
- **Clé nécessaire** : non.

Recommandation : source de relecture humaine uniquement.

## Sources écartées

| Source | Raison de l'écart |
| --- | --- |
| Scraping HTML Légifrance, Code du travail numérique, INSEE ou Service-public.fr | Fragile, contraire aux contraintes de la PR, risque de rupture sur changement d'interface. |
| Sites commerciaux, cabinets, blogs, bases juridiques privées | Licence et pérennité incompatibles avec une veille institutionnelle autonome. |
| OpenLegi, bibliothèques ou MCP tiers non officiels | Peuvent aider au prototypage local, mais ne sont pas la source officielle et ajoutent un intermédiaire. |
| Réutilisations data.gouv non institutionnelles sur le SMIC | Compilation utile, mais producteur non officiel et qualité variable. |
| PDF isolés de centres de gestion ou associations | Bon support documentaire ponctuel, mauvais support d'automatisation durable. |

## Prototype livré dans cette PR

Le prototype `HttpJsonRegulatorySourceFetcher` récupère une source JSON officielle, normalise le contenu et produit un `RegulatorySnapshot`. Il est volontairement limité à une source JSON sans authentification, par exemple la fiche data.gouv de l'API Légifrance, afin de valider l'architecture sans clé PISTE et sans toucher aux règles métier.

Ce prototype :

- ne contient aucune règle CCNS ;
- n'interprète pas les montants, dates d'effet ou avenants ;
- ne modifie pas les grilles salariales ;
- accepte un transport injectable pour simuler les appels réseau en test ;
- prépare le futur raccord PISTE ou Journal officiel avec la même interface de récupération.

## Architecture actuelle

Le socle existant est adapté :

- `RegulatoryReference` décrit la source officielle à surveiller ;
- `RegulatorySnapshot` stocke un hash, une taille, une date de récupération et des métadonnées ;
- `RegulatoryWatchService` orchestre récupération, comparaison et stockage sans effet métier ;
- `JsonRegulatorySnapshotStore` suffit pour un historique minimal append-only.

Ajustements recommandés, sans urgence :

1. ajouter plus tard un fetcher PISTE authentifié distinct du fetcher JSON générique ;
2. introduire un registre de références réglementaires versionné pour éviter de disperser les URLs ;
3. enrichir les métadonnées avec identifiant Légifrance, fonds (`KALI`, `JORF`, `LEGI`), date de publication, date d'effet et nature du texte ;
4. prévoir un cache et une limitation de fréquence par source avant tout appel planifié ;
5. conserver la validation humaine comme frontière obligatoire avant application métier.

## Prochaines intégrations recommandées

1. Obtenir des identifiants PISTE pour Teamworks-CCNS.
2. Prototyper un fetcher Légifrance stable sur une seule requête `KALI` liée à l'IDCC 2511.
3. Ajouter des tests simulant l'OAuth et les réponses JSON PISTE.
4. Étendre ensuite aux arrêtés d'extension `JORF` liés aux avenants CCNS.
5. Ajouter une veille SMIC fondée sur les textes JORF, puis un contrôle documentaire INSEE.
6. Ajouter la veille CEE sur les articles du Code de l'action sociale et des familles et leurs textes modificateurs.

## Risques identifiés

- Les quotas PISTE peuvent imposer un cache strict et une fréquence quotidienne plutôt qu'à chaque lancement de l'application.
- Les résultats de recherche Légifrance doivent être désambiguïsés pour éviter de confondre un commentaire, un texte abrogé ou une convention homonyme avec la CCNS IDCC 2511.
- Les dates d'effet ne sont pas toujours identiques aux dates de publication ; elles doivent rester soumises à validation humaine.
- Le SMIC peut différer selon périmètre géographique, notamment Mayotte ; le périmètre Teamworks-CCNS doit être explicite.
- Les textes CEE expriment la rémunération en multiple du SMIC horaire : une modification du SMIC et une modification du coefficient CEE sont deux alertes distinctes.
