# Matrice de compatibilité Teamworks-CCNS

## Objectif

Cette matrice rend explicites les environnements à préserver avant une évolution technique, une optimisation ou une mise à jour de dépendance. Elle complète les règles de pérennité technique et ne remplace pas les tests réels sur poste cible.

## Environnements cibles

| Axe | Cible à préserver | Vérifications attendues | Points de vigilance |
| --- | --- | --- | --- |
| Windows poste utilisateur | Windows 11 | lancement, installation des dépendances, accès fichiers, impression/export, écrans wxPython principaux | chemins avec espaces, encodage, droits utilisateur, antivirus, DLL natives |
| Windows serveur | Versions récentes de Windows Server | lancement applicatif, accès base locale ou réseau, sessions multiples si l'usage existe | bureau distant, profils utilisateurs, latence réseau, verrouillage SQLite/MySQL |
| Linux | Distributions maintenues | installation `pip`, lancement des modules non graphiques et, si disponible, interface wxPython | paquets système wxPython, casse des chemins, dépendances binaires |
| macOS Intel | Versions récentes de macOS | installation, lancement, accès fichiers, dépendances graphiques | permissions système, chemins, packaging, disponibilité des roues binaires |
| macOS Apple Silicon | Versions récentes de macOS sur ARM | installation native ou stratégie documentée si une dépendance impose Rosetta | roues Python ARM, OpenCV, wxPython, Pillow, packaging |
| Python | Versions récentes et supportées de Python | absence d'API supprimée, absence de syntaxe trop ancienne ou trop récente sans justification | le README historique mentionne Python 3.7+, mais les évolutions doivent viser des versions maintenues |
| Base locale | SQLite ou moteur local réellement configuré | ouverture, requêtes, commits, fermeture, performances sur base représentative | coût faible d'ouverture possible, verrouillage fichier, taille de base |
| Base réseau | SQLite sur partage ou MySQL via configuration réseau | latence, reconnexion, erreurs transitoires, concurrence lecture/écriture | ne pas supposer qu'une connexion globale est préférable |
| Bureau distant | RDP ou solution équivalente | temps perçu, rendu des listes, images, rafraîchissements wxPython | le rendu peut coûter plus cher que la requête SQL |

## Dépendances actuelles à surveiller

| Dépendance | Usage probable | Compatibilité à vérifier avant changement | Risque principal |
| --- | --- | --- | --- |
| wxPython | interface graphique | roues disponibles par OS, version Python supportée, comportement en bureau distant | dépendance native lourde, packaging variable selon plateformes |
| Pillow | images | API dépréciées, roues Windows/Linux/macOS Intel/ARM | renommages ou suppressions d'API historiques |
| matplotlib | graphiques | backend utilisé, dépendances natives, taille au packaging | import coûteux et backends non utiles |
| numpy | calculs et dépendances indirectes | roues par architecture, cohérence avec OpenCV/matplotlib | dépendance native structurante |
| opencv-python | image/vision | disponibilité par OS/architecture, poids, alternatives si usage limité | dépendance lourde, packaging Apple Silicon/Linux |
| mysql-connector-python | accès MySQL | version Python, TLS, reconnexion, timeouts | différences avec SQLite et réseau instable |
| pypiwin32 | intégration Windows | usage isolé et optionnel hors Windows | dépendance spécifique Windows à ne pas importer globalement sur autres OS |
| pycryptodome | cryptographie | roues, API maintenues, usages sûrs | compatibilité binaire et sécurité |
| reportlab, XlsxWriter, icalendar | exports | encodage, formats produits, compatibilité Python | régressions d'export ou dépendance non nécessaire au démarrage |
| mailjet-rest | envoi courriel | API externe, réseau, erreurs et timeouts | ne pas bloquer le lancement ni l'interface |
| python-dateutil, six, appdirs | utilitaires | nécessité actuelle, alternatives standard si possible | dette de compatibilité si usage devenu inutile |

## Grille de décision avant ajout ou mise à jour

| Question | Réponse attendue avant validation |
| --- | --- |
| La dépendance est-elle maintenue et documentée ? | Oui, avec source vérifiable. |
| La licence est-elle compatible avec le projet ? | Oui, et le doute est documenté. |
| Des roues existent-elles pour les plateformes cibles ? | Oui, ou une stratégie d'installation est documentée. |
| L'API utilisée est-elle publique et non dépréciée ? | Oui, ou un plan de remplacement est prévu. |
| Une dépendance existante ou la bibliothèque standard suffit-elle ? | Non, ou la justification est explicite. |
| Le coût au démarrage et au packaging est-il acceptable ? | Oui, ou l'import est différé. |
| Les tests couvrent-ils le comportement concerné ? | Oui, au moins par vérification ciblée. |

## Vérifications minimales par type de changement

| Changement | Vérifications minimales |
| --- | --- |
| Optimisation SQL ou accès base | comparer résultats métier, nombre de requêtes, durée SQL/fetch, comportement local et réseau si concerné |
| Cache ou réutilisation de connexion | vérifier invalidation, fermeture, perte réseau, concurrence et retour arrière |
| Modification wxPython | vérifier absence de blocage au lancement, rendu initial, rafraîchissement, sélection et usage en bureau distant si possible |
| Mise à jour de dépendance | vérifier installation propre, imports, API dépréciées, plateformes cibles et exports associés |
| Modernisation Python | vérifier compatibilité avec la plage de versions retenue, warnings de dépréciation et absence de syntaxe excluante inutile |
| Packaging | vérifier `setup.py`, chemins de ressources, DLL/bibliothèques natives et nommage sensible à la casse |

## Écarts connus à traiter

- La documentation d'installation mentionne encore Python 3.7 ou plus, alors que Python 3.7 n'est plus une cible moderne maintenue. Une future passe doit fixer une plage de versions supportées après test des dépendances graphiques et binaires.
- `setup.py` contient un chemin de build `exe.win32-3.7` et des références DLL liées à une génération historique ; ce point doit être réévalué avant tout packaging moderne.
- Les dépendances ne sont pas épinglées dans `requirements.txt`. Toute stabilisation doit éviter un gel arbitraire sans test multiplateforme.
