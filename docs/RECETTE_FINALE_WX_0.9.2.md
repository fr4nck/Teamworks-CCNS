# wx 0.9.2 — registre d'exécution de la recette finale

**Ouvert le :** 11 novembre 2026 — **Statut : qualification métier incomplète, stable non autorisée.**

Ce document est un **registre des contrôles effectivement réalisés**, non une deuxième roadmap. La décision de gel et les critères de sortie restent définis uniquement dans [`ROADMAP.md`](../ROADMAP.md), sections « Décision active » et 16 à 18.

## Référence immuable de la préversion

- [Release `v0.9.2-rc12`](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12) : préversion publique avec ZIP portable, installateur Windows x64 et `SHA256SUMS.txt`.
- Code du candidat : `9b02fbe94016b403255eabdaa856176d7f3e0ac5`.
- [CI `42675793471`](https://github.com/fr4nck/Teamworks-CCNS/actions/runs/42675793471) : 2 902 tests PASS, 12 SKIP, tests Windows et packaging SUCCESS.
- Démarrage réel : portable ouvert sous Windows 11 sur 5700X ; configuration de connexion déjà présente reconnue. **Le profil habituel n'est pas une base de test isolée.**

## Résultats actuellement établis

| Réf. | Contrôle | Résultat | Fondement |
| --- | --- | --- | --- |
| P0 | Provenance du build, manifestes, `VERSION`, `BUILD.txt` | PASS | Même commit que l'artefact qualifié |
| P1 | Tests Python, parcours simulés Windows, packaging | PASS | CI `42675793471` |
| P2 | Démarrage réel de RC12, récupération des paramètres du profil | PASS limité | Retour utilisateur ; **aucune écriture métier vérifiée** |
| P3 | Précontrôle local renouvelé du portable | **PASS — 11/11/2026** | 5700X, PowerShell 5.1 : version/commit conformes ; **2 278/2 278** fichiers SHA-256 PASS ; rapport local `preflight-rc12-20261111-160030-c8e38994.json` ; contrôle sans lancement, SQL ni courriel |
| B0 | Copie de base indépendante et sauvegarde de secours vérifiées | **BLOQUÉ — isolation MySQL non démontrée** | Le 11/11/2026, lecture **locale et sans connexion SQL** de `AppData/Roaming/teamworks/Config.json` : `nomFichier` contient `[RESEAU]`, ce qui sélectionne **MySQL/MariaDB réseau** dans `GestionDB.py`. Serveur, droits, données et sauvegardes non audités. Avant toute écriture : profil de recette distinct, base MySQL de test séparée et droits limités, données fictives, sauvegarde et plan de retour arrière |
| B1 | Fiche salarié, neuf onglets, navigation et fermeture | NON TESTÉ | Pas de recette complète documentée |
| B2 | Écriture fictive sur copie, enregistrement, redémarrage et persistance | NON TESTÉ | Ne jamais écrire sur la base de production pour tester |
| B3 | Contrats CDI/CDD/CEE, renouvellement et transformation, DPAE/DUE | NON TESTÉ | Parcours complet sur copie manquant |
| B4 | Sauvegarde **et restauration** intégrales sur copie | NON TESTÉ | Les tests CI n'équivalent pas à une restauration utilisateur |
| B5 | Word/Writer, publipostage, impression | NON TESTÉ | Vérification sur poste Windows nécessaire |
| B6 | Présences, recrutement, frais, préférences et administration | NON TESTÉ | Vérification métier sur copie nécessaire |
| U1 | Rendu Windows et DPI 100/125/150 %, souris/clavier, fermeture | NON TESTÉ | Pas de recette utilisateur complète |
| M1 | Mailer complet, fenêtres modales et focus | NON TESTÉ | Bancs natifs fictifs PASS, pas l'application complète |
| M2 | SMTP/HTTP local instrumenté, déconnexion, refus, incertitude | NON TESTÉ | Interdit de tester avec véritables destinataires |
| F1 | Absence de bloqueur/majeur, période contrôlée, retour arrière | NON TESTÉ | Pas de procès-verbal de recette |
| F2 | Décision explicite de passer en version stable | NON DONNÉ | Gel fonctionnel approuvé, **pas** la stable |

## Identification du moteur de données — contrôle du 11 novembre 2026

- Sur le 5700X, le fichier de configuration du **profil Windows courant** contient un `nomFichier` avec le marqueur `[RESEAU]`. La lecture par PowerShell n'a ouvert **aucune connexion SQL**, n'a extrait **aucun secret** et n'a modifié **aucune base**.
- Dans `teamworks/GestionDB.py`, `[RESEAU]` active le chemin **MySQL/MariaDB**. Un `nomFichier` local sans ce marqueur sélectionnerait SQLite ; cette deuxième hypothèse **ne décrit donc pas la configuration courante**.
- Le moteur effectivement contacté, la disponibilité du serveur, les droits d'écriture, la base sélectionnée en session et le contenu des données **ne sont pas vérifiés**. Ne publier ni `Config.json`, ni chaîne `nomFichier`, ni adresse de serveur, ni identifiant ou mot de passe dans un journal GitHub.
- **Séquence B0 à valider avant toute recette métier** : préparer une base **MySQL/MariaDB de test indépendante** (préférer un serveur local isolé, des données fictives et un utilisateur SQL limité au jeu de test), créer un **profil/configuration Windows de recette distinct**, puis confirmer que l'application ne voit aucun serveur/base de production et que la restauration de secours fonctionne. Le seul dossier portable distinct **n'isole pas** le profil utilisateur ni la configuration.

## Exécution — ordre impératif

1. **P3 : FAIT le 11/11/2026** sur le portable déjà extrait au 5700X ; 2 278 fichiers vérifiés en SHA-256, version et commit corrects. Rapport enregistré localement dans `C:\_Atelier_IA\Teamworks-CCNS\Stabilisation-wx-0.9.2\preflight-rc12-20261111-160030-c8e38994.json`. Aucune donnée métier n'a été ouverte ni modifiée par le contrôle.
2. **B0 : isoler MySQL/MariaDB avant tout test en écriture.** Le 5700X conserve une configuration réseau existante, potentiellement de production : ne pas l'utiliser pour la recette. Préparer un serveur et une base de test séparés, un compte SQL dédié et un profil Windows de recette indépendant, puis vérifier sauvegarde/restauration **sur la base de test seulement**. Le portable dans un dossier différent ne suffit pas.
3. **B1 à B6, U1 :** exécuter sur la copie les opérations réellement utilisées par l'association. Relever précisément les résultats, sans exposer identifiants, salariés, coordonnées ni données RH dans GitHub.
4. **M1–M2 :** uniquement sur jeu fictif et transport local instrumenté. Aucun mail réel ; un SMTP de production « pour essayer » n'est pas acceptable.
5. **F1–F2 :** qualifier les anomalies, les corriger avec tests si confirmées, reconstruire depuis un nouveau commit si le code change, puis recueillir une décision expresse pour `v0.9.2`.

## Points techniques identifiés

- `tools/recette_windows/run_local.ps1` automatise seulement une partie des interactions souris/clavier, **depuis les sources**, avec le profil Windows courant. Il **n'est pas isolant** ; ne pas l'utiliser comme preuve B0 ou B2 sur le profil relié à la production.
- Le scénario `tools/smoke_pmsl_contracts_21h.py`, historiquement non qualifié sur un ancien jalon, nécessite une exécution sur base fictive. Son état ne démontre **pas** un bug de RC12 tant qu'il n'est pas reproduit.
- Le rapport TW-UI-01 Phase 3 qualifie les transports fictifs et la progression wx mais **pas** les coupures réseau réelles ni les envois de bout en bout.
- Aucune nouvelle fonction wx pendant le gel sans dérogation explicite et documentée. `master` et `qt/master` hors de ce périmètre.

## Registre d'anomalies et décision

Toute anomalie confirmée : date, système, SHA du candidat, écran, action, attendu, observé, reproduction, gravité (BLOQUANT / MAJEUR / MINEUR / COSMÉTIQUE), preuve **anonymisée**, correction, requalification. Ne pas téléverser de ZIP de rapport s'il contient des captures/dumps d'identifiants ou données personnelles.

**Décision actuelle : GO pour la recette ; NO GO pour `v0.9.2` stable.** Rien n'autorise à modifier le tag RC12 publié.
