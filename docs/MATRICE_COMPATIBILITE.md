# Matrice de compatibilité Teamworks-CCNS

**Mise à jour : 7 août 2026**

## Objectif

Cette matrice distingue les environnements **réellement exercés** des plateformes seulement visées à terme. Elle complète `ROADMAP.md` et ne remplace jamais une recette sur poste cible.

## Environnements et niveau de preuve

| Axe | État actuel | Preuve disponible | Reste à valider |
| --- | --- | --- | --- |
| Python | **3.11 = version de référence actuelle** | CI Linux et Windows sur Python 3.11 | toute autre version avant qualification |
| Ubuntu / Linux | **Automatisé** | Ubuntu 24.04 : compilation, audits, tests | interface graphique complète sur poste Linux si cible utilisateur |
| Windows CI | **Automatisé** | Windows Server 2022 : parcours critiques wxPython + packaging | ne remplace pas Windows poste utilisateur |
| Windows 11 poste utilisateur | **Cible prioritaire, validation manuelle incomplète** | tests ponctuels déjà réalisés sur certains dialogues | parcours minimal complet sur copie de base réelle |
| Windows portable sans Python | **Build automatisé** | PyInstaller, smoke de démarrage, manifeste et SHA-256 | utilisation réelle complète après décompression |
| Windows Server en usage applicatif | **Non qualifié** | runner CI uniquement | sessions, impression, réseau, droits, base réelle |
| macOS Intel | **Non qualifié** | aucune CI actuelle | dépendances, wxPython, lancement et packaging |
| macOS Apple Silicon | **Non qualifié** | aucune CI actuelle | roues ARM, wxPython, dépendances natives, packaging |
| SQLite locale | **Partiellement automatisé** | préflight lecture seule, quick_check, tests fonctionnels et sauvegarde/restauration automatisés | parcours utilisateur complet sur copie réelle |
| SQLite sur partage réseau | **Non qualifié** | aucune preuve suffisante | latence, verrouillage, concurrence et récupération après coupure |
| MySQL / réseau | **Non qualifié comme cible de pré-release** | connecteur historique présent dans le code | connexion réelle, TLS, timeouts, reconnexion, concurrence |
| Bureau distant | **Non qualifié** | aucune recette dédiée actuelle | rendu wxPython, listes, rafraîchissements et latence perçue |

## Dépendances structurantes

| Dépendance | Rôle | État / règle actuelle | Risque principal |
| --- | --- | --- | --- |
| wxPython | interface graphique | exercé dans les parcours Windows ; version installée via les dépendances du projet | comportement graphique et disponibilité des roues |
| PyInstaller | packaging Windows | **6.16.0** figé pour le build CI | packaging, hooks, imports dynamiques |
| pytest | tests CI | **8.4.1** figé dans `.github/requirements-ci.txt` | évolution des plugins/comportements de tests |
| six | compatibilité historique résiduelle | **1.17.0** dans le job de tests ; dette en réduction | dette de compatibilité historique |
| numpy | calculs / dépendances indirectes | packaging corrigé pour les API NumPy 2 | modules internes et compatibilité binaire |
| Pillow | images | conservé dans le packaging | API dépréciées et ressources graphiques |
| matplotlib | graphiques | collecté dans le paquet Windows | poids et backends inutiles |
| reportlab | PDF | collecté dans le paquet Windows | régressions d’export / packaging |
| mysql-connector-python | accès MySQL | import explicitement prévu au build | réseau, TLS, reconnexion |
| win32com / intégration Windows | fonctions Windows historiques | import explicitement prévu au build | dépendance spécifique Windows |
| XlsxWriter / exports | exports tableurs | parcours export couvert par smoke/tests ciblés | formats, encodage, boîtes de dialogue |

## Politique Python

L’ancienne documentation « Python 3.7 ou plus » est obsolète.

**Python 3.11 est la seule version actuellement qualifiée par la CI.** Une extension de la plage de versions supportées nécessite :

1. disponibilité des roues wxPython et dépendances natives ;
2. compilation complète ;
3. suite de tests ;
4. parcours Windows critiques ;
5. packaging ;
6. recette utilisateur si la version devient une cible officielle.

## Packaging Windows

Le paquet Windows actuel est produit sur Windows Server 2022 avec Python 3.11 et PyInstaller 6.16.0.

Les contrôles automatisés comprennent :

- inventaire d’au moins 250 modules internes ;
- inclusion des familles `Ctrl`, `Dlg`, `Ol`, `Utils`, `CcnsCore`, `domain`, `application` et `infrastructure` ;
- présence des ressources essentielles ;
- smoke de démarrage de l’exécutable ;
- manifeste de contenu UTF-8 ;
- vérification des empreintes SHA-256 de chaque entrée ;
- somme SHA-256 de l’archive ;
- liste des dépendances réellement utilisées lors du build.

Le build ne constitue pas à lui seul une qualification Windows 11 utilisateur.

## Interface wxPython

Les modifications récentes couvrent notamment :

- parentage de dialogues et sizers ;
- largeurs ObjectListView converties en entiers ;
- sélections multiples natives wxPython ;
- filtres de recrutement sans `exec()` fragile ;
- dates historiques normalisées avant affichage dans les champs masqués ;
- thème Système / Clair / Sombre ;
- échelle de police 80–200 %.

Toute modification wxPython doit au minimum préserver : démarrage, affichage, sélection, validation et fermeture des dialogues concernés.

## Encodages et fichiers historiques

Le socle textuel suivi est désormais en UTF-8. Les anciens encodages ne sont tolérés qu’aux frontières où des données ou profils historiques peuvent encore exister.

Les règles sont :

- UTF-8 pour les sources et nouveaux fichiers ;
- conservation contrôlée d’un encodage historique lorsqu’un profil utilisateur existant doit être réécrit sans corruption ;
- aucune réparation de mojibake arbitraire à l’affichage ;
- chemins Windows avec accents à considérer comme cas normal.

## Dates et bases existantes

Les lots TW-136, TW-139 et TW-140 ont remplacé les conversions par découpage de chaînes par un normaliseur central et ont fiabilisé les champs masqués.

Aucune migration destructive des valeurs historiques n’a été réalisée. Les valeurs existantes sont lues de façon tolérante ; les futures écritures doivent tendre vers le format ISO canonique.

## Grille de décision avant ajout ou mise à jour

| Question | Réponse attendue avant validation |
| --- | --- |
| La dépendance est-elle maintenue et documentée ? | Oui, avec source vérifiable. |
| La licence est-elle compatible avec le projet ? | Oui, ou le doute est documenté. |
| Des roues existent-elles pour Python 3.11 et la plateforme cible ? | Oui, ou une stratégie explicite existe. |
| L’API utilisée est-elle publique et non dépréciée ? | Oui, ou un plan de remplacement existe. |
| Une dépendance existante ou la bibliothèque standard suffit-elle ? | Non, ou la justification est explicite. |
| Le coût au démarrage et au packaging est-il acceptable ? | Oui, ou l’import est différé. |
| Les tests couvrent-ils le comportement concerné ? | Oui, au moins par vérification ciblée. |
| La plateforme annoncée a-t-elle été réellement exercée ? | Oui avant de la déclarer supportée. |

## Écarts connus avant pré-release

- Windows 11 doit encore être validé sur le **parcours minimal complet** avec une copie de base réelle.
- La PR #209 d’audit runtime reste en brouillon jusqu’à sa recette Windows manuelle.
- macOS, Apple Silicon, Windows Server en usage réel, bases réseau et bureau distant ne doivent pas être présentés comme qualifiés.
- `requirements.txt` n’est pas assimilé à une garantie multiplateforme : les dépendances du build et de la CI sont figées séparément lorsque la reproductibilité l’exige.

Toute annonce de compatibilité doit rester cohérente avec cette matrice et avec `ROADMAP.md`.
