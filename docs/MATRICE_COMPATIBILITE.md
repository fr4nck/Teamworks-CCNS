# Matrice de compatibilité Teamworks-CCNS

## Objectif

Cette matrice rend explicites les environnements à préserver avant une évolution technique, une optimisation ou une mise à jour de dépendance. Elle complète les règles de pérennité technique et ne remplace pas les tests réels sur poste cible.

## État de qualification par plateforme

Le tableau ci-dessous distingue ce qui est automatisé en CI, ce qui a fait l'objet d'une recette utilisateur réelle, et ce qui reste expérimental.

| Plateforme | État CI | Recette utilisateur | Remarques |
| --- | --- | --- | --- |
| **Windows 10/11 poste** | ✅ job `windows-smokes` (compilation, smoke wx, tests TW-139, parcours critiques) | ✅ recette réelle (Franck, 30/07/2026) sur Python 3.11 / wxPython 4.2.5 | Cible prioritaire. Parcours Frais, Rapports, Impression non encore validés manuellement. |
| **Windows Server récent** | ⚠️ non couvert en CI | ❌ non qualifié | Bureau distant, sessions multiples et accès réseau MySQL à vérifier avant déploiement serveur. |
| **Linux x64 (Ubuntu 24.04)** | ✅ job `tests` (compilation, pytest, audits) | ❌ GUI utilisateur non qualifiée | Interface wxPython non exercée sur poste Linux réel ; modules non graphiques automatisés. |
| **macOS Intel** | ⚠️ job `macos-smokes` conditionnel (compilation + smoke wx + tests TW-139) uniquement si changements GUI/dépendances | ❌ recette utilisateur absente | CI automatisée ≠ qualification utilisateur. Pas de paquet macOS produit automatiquement. |
| **macOS Apple Silicon (M1/M2/M3)** | ✅ runner `macos-14` (ARM64) utilisé pour le job `macos-smokes` | ❌ recette utilisateur absente | wxPython 4.2.x fournit des roues ARM64 pour macOS. OpenCV et pypiwin32 non installés sur macOS (hors scope). |
| **Linux ARM64 / Raspberry Pi** | ❌ non couvert en CI (voir note ci-dessous) | ❌ non qualifié | Cible expérimentale. Procédure de recette manuelle documentée ci-dessous. |

## Environnements cibles (détail)

| Axe | Cible à préserver | Vérifications attendues | Points de vigilance |
| --- | --- | --- | --- |
| Windows poste utilisateur | Windows 11 | lancement, installation des dépendances, accès fichiers, impression/export, écrans wxPython principaux | chemins avec espaces, encodage, droits utilisateur, antivirus, DLL natives |
| Windows serveur | Versions récentes de Windows Server | lancement applicatif, accès base locale ou réseau, sessions multiples si l'usage existe | bureau distant, profils utilisateurs, latence réseau, verrouillage SQLite/MySQL |
| Linux x64 | Distributions maintenues | installation `pip`, lancement des modules non graphiques et, si disponible, interface wxPython | paquets système wxPython, casse des chemins, dépendances binaires |
| macOS Intel | Versions récentes de macOS | installation, lancement, accès fichiers, dépendances graphiques | permissions système, chemins, packaging, disponibilité des roues binaires |
| macOS Apple Silicon | Versions récentes de macOS sur ARM | installation native (roues ARM64 disponibles pour wxPython 4.2.x) | pypiwin32 non disponible sur macOS ; opencv-python installable mais non requis |
| Python | 3.11 (cible actuelle), 3.12 à vérifier avant adoption | absence d'API supprimée, absence de syntaxe trop ancienne ou trop récente sans justification | le README historique mentionne Python 3.7+, mais les évolutions doivent viser des versions maintenues |
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

## Linux ARM64 / Raspberry Pi — état et procédure de qualification

### État actuel

Aucun runner GitHub Actions ARM64 adapté au projet n'est utilisé (émulation QEMU exclue pour cause de surcoût et de latence incompatibles avec les smoke tests wxPython). Linux ARM64 est donc une **cible expérimentale non qualifiée**.

### Analyse de compatibilité des dépendances

| Dépendance | ARM64 Raspberry Pi OS 64 bits | Risque / remarque |
| --- | --- | --- |
| Python 3.11 | ✅ disponible via `apt` sur Raspberry Pi OS Bookworm 64 bits | Version 3.11 ou 3.12 disponible |
| wxPython 4.2.x | ⚠️ aucune roue PyPI ARM64 pour Linux disponible ; compilation depuis les sources nécessaire | Durée de compilation > 2 h sur Pi 4 ; alternative : paquet système `python3-wxgtk4.0` si disponible |
| Pillow | ✅ roues disponibles sur PyPI pour `manylinux` ARM64 | |
| numpy | ✅ roues disponibles | |
| matplotlib | ✅ roues disponibles | |
| reportlab | ✅ roues disponibles | |
| XlsxWriter | ✅ pur Python | |
| mysql-connector-python | ✅ roues disponibles | |
| pypiwin32 | ❌ dépendance Windows uniquement ; les imports `win32*` sont protégés par des gardes OS dans le code | À vérifier que tous les imports win32 sont optionnels ou limités à `sys.platform == "win32"` |
| pycryptodome | ✅ roues disponibles | |
| opencv-python | ⚠️ roues disponibles mais lourdes ; à vérifier si l'usage est optionnel | |

**Conclusion** : le principal bloquant est wxPython, pour lequel aucune roue ARM64 PyPI n'est publiée. Un déploiement sur Raspberry Pi nécessite soit la compilation depuis les sources, soit l'utilisation du paquet système, soit l'abandon de l'interface graphique sur ce matériel.

### Procédure de recette manuelle sur Raspberry Pi 4 / Pi 5

À exécuter sur un Raspberry Pi 4 ou Pi 5 sous Raspberry Pi OS Bookworm 64 bits avant toute annonce de support :

```bash
# 1. Vérifier Python 3.11
python3.11 --version

# 2. Installer les dépendances non graphiques
pip install --requirement requirements/python311-core.txt

# 3. Vérifier l'installation de wxPython (paquet système ou compilation)
#    Option A : paquet système
sudo apt-get install python3-wxgtk4.0
#    Option B : compilation depuis les sources (longue, > 2 h)
pip install --no-binary wxPython wxPython>=4.2,<4.3

# 4. Compiler les modules Python
python -m compileall -q teamworks/Ctrl teamworks/Dlg teamworks/Ol

# 5. Exécuter les tests ciblés
python -m pytest -q tests/test_tw139_runtime_guards.py

# 6. Smoke wx.App
python - <<'PY'
import wx
app = wx.App(False); app.Destroy()
print("wx.App OK")
PY

# 7. Parcours manuel : démarrage, accueil, individus, présences, recrutement
python teamworks/Teamworks.py
```

Le résultat de cette recette doit être consigné dans ce document avant toute annonce de support Raspberry Pi.
