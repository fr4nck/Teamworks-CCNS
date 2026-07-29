# Teamworks-CCNS — Roadmap RC1 Windows

Mise à jour : 29 juillet 2026

## Objectif

Produire une première pré-release Windows réellement testable de Teamworks-CCNS à partir de `master`, sans ouvrir de nouveau chantier métier avant validation du socle.

Version cible : `v0.9.0-rc1`.

## État du socle

- TW-119 : préférences d’affichage, thème Système / Clair / Sombre et échelle 80–200 % — fusionné.
- TW-120 : diagnostics d’installation et de démarrage Windows — fusionné.
- TW-121 : validation des préférences d’affichage Windows — fusionné.
- TW-122 : application, vérification et restauration sûre des profils d’affichage — fusionné.

## TW-123 — Packaging reproductible Windows

### Livrables attendus

- `Teamworks-CCNS-v0.9.0-rc1-Windows-x64.zip` ;
- exécutable principal Teamworks-CCNS ;
- dossier de ressources complet ;
- fichier `VERSION` ;
- fichier `SHA256SUMS.txt` ;
- journal de construction conservé comme artefact GitHub Actions.

### Critères de sortie

- build lancé depuis un runner Windows propre ;
- dépendances Python figées ;
- ressources, traductions, icônes et fichiers de configuration inclus ;
- aucun chemin absolu issu du poste de développement ;
- démarrage possible depuis un dossier sans Python installé ;
- échec de build explicite si une ressource obligatoire manque ;
- artefact téléchargeable depuis GitHub Actions.

## TW-124 — Validation du premier lancement

- démarrage sans base configurée ;
- choix ou création du dossier de données ;
- ouverture d’une base Teamworks existante ;
- diagnostic lisible en cas de module, ressource ou base manquante ;
- création des journaux dans un dossier utilisateur accessible ;
- fermeture propre sans processus résiduel.

## TW-125 — Validation métier minimale

La RC1 doit permettre de contrôler au minimum :

- accueil ;
- ouverture d’une base ;
- fiche salarié ;
- contrats et classifications ;
- contrôles CCNS ;
- dossiers incomplets ;
- exports ;
- thème Système / Clair / Sombre ;
- échelle d’affichage ;
- persistance des réglages ;
- fermeture propre.

Les anomalies découvertes seront corrigées par lots ciblés. Aucune refonte large ne doit bloquer la RC1.

## TW-126 — Publication de la pré-release

Publication GitHub en mode pré-release avec :

- ZIP Windows x64 ;
- sommes SHA-256 ;
- notes de version ;
- limites connues ;
- procédure de sauvegarde avant essai ;
- procédure de retour à la version précédente.

## Passage à la version stable

La version `v1.0.0` sera envisageable après :

1. installation ou extraction sur le poste Windows de production ;
2. ouverture réussie d’une copie de la base réelle ;
3. validation des parcours essentiels ;
4. correction des anomalies bloquantes et majeures ;
5. nouveau build reproductible au vert.

## Règle de priorité jusqu’à RC1

Ordre obligatoire :

1. build Windows ;
2. démarrage ;
3. ouverture de base ;
4. parcours essentiels ;
5. publication RC1.

Les nouvelles fonctions métier, intégrations Noethys/Dolibarr, congés, pointage et évolutions majeures d’interface restent planifiées après la RC1 sauf correction nécessaire à son utilisation.
