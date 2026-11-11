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
| P3 | Précontrôle local renouvelé du portable | À exécuter | `tools/recette_windows/preflight_rc12.ps1` |
| B0 | Copie de base indépendante et sauvegarde de secours vérifiées | NON TESTÉ | Pas d'identification d'une base de recette |
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

## Exécution — ordre impératif

1. **P3 : précontrôle en lecture seule**, sur le portable déjà extrait au 5700X. Lancer `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\recette_windows\preflight_rc12.ps1` depuis une copie à jour de `wx/master`, ou télécharger ce script depuis le commit qui l'a introduit. Le contrôle ne lance pas Teamworks, n'accède à aucune base et ne supprime aucun fichier.
2. **B0 : figer une copie de base** et un plan de restauration, distincts de l'exploitation. Ni le fait que le portable soit dans un autre dossier, ni un simple changement de nom de dossier ne suffisent : Teamworks réemploie les paramètres du profil Windows.
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
