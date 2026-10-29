# Teamworks — suivi UI/UX / thème graphique

**Mise à jour : 27 août 2026**

## Objectif

Ce fichier suit la **modernisation graphique et ergonomique** de Teamworks-CCNS indépendamment de la migration Python 3 et des fonctions métier CCNS.

## Règle de classement

- défaut historique déjà présent dans Teamworks Vanilla → `01_VANILLA_BUGFIX.md` ;
- incompatibilité imposée par Python 3/wxPython Phoenix → `02_PYTHON3_PHOENIX.md` ;
- anomalie créée par le thème, le zoom, les tokens, les nouvelles dimensions ou les nouveaux composants → ce fichier ;
- comportement métier nouveau → `04_CCNS_EXTENSIONS.md`.

Les correctifs de contrôleurs/listes intervenant après introduction de `section.GetContentPanel()`, des tokens sémantiques ou d'un nouveau découplage owner/parent sont classés ici, et non comme bugs Vanilla.

## Méthode de mesure

Le chantier est découpé en **9 jalons de poids égal**. Un jalon peut être `Terminé`, `Partiel` (0,5 point) ou `À valider` (0 point).

| Jalon | État | Situation actuelle |
|---|---|---|
| 1. Design system / tokens sémantiques | Terminé | couleurs, métriques et rôles centraux présents |
| 2. Thèmes Clair / Sombre / Système | Terminé | moteur central et comportement Système Windows verrouillés |
| 3. Échelle globale 80–200 % | Terminé | source unique d'échelle et métriques communes |
| 4. Composants communs | Terminé | boutons, textes, sections et helpers raccordés au design system |
| 5. Navigation principale modernisée | Terminé | socle TW-189 fusionné |
| 6. Branding / organisation / préférences visuelles | Terminé | branding Teamworks CCNS, logo organisation et préférences consolidés |
| 7. Migration des écrans historiques vers le nouveau langage visuel | Partiel | modernisation déjà étendue, mais encore progressive selon les écrans |
| 8. Suppression des rigidités historiques (tailles, séparateurs, grands vides, layouts) | Partiel | nombreux correctifs intégrés ; validation écran par écran encore nécessaire |
| 9. Validation visuelle réelle Windows | À valider | lisibilité, textes tronqués, mode Système, zoom et densité doivent encore être vérifiés sur le portable final |

## Avancement

6 jalons terminés + 2 jalons partiels sur 9 :

**UI/UX / thème graphique : 7 / 9 = 77,8 %, arrondi à 78 %.**

Ce pourcentage ne signifie pas que tous les écrans sont visuellement parfaits. Le socle commun est largement en place ; le reste est principalement la finition des écrans historiques et la validation réelle du rendu Windows.

## Restant prioritaire

- vérifier les principaux écrans à l'échelle utilisée réellement ;
- repérer les textes tronqués et séparateurs encore rigides ;
- supprimer les grands espaces inutiles sans ajouter de surcouches locales ;
- contrôler les sélections, états désactivés et contrastes en clair/sombre ;
- ne corriger que via les composants/tokens centraux lorsqu'un défaut est transversal ;
- geler les retouches purement cosmétiques lourdes jusqu'après la première recette exploitable.

## Préférences d'affichage

Le crash de la version `0.9.0` à l'ouverture des préférences provenait d'une
compréhension Python 3 placée dans la classe du dialogue et référençant une
table de libellés définie dans cette même portée de classe. La table est désormais
au niveau du module, le dialogue est ouvert par le parcours Windows réel et un
garde AST recherche cette famille de défauts dans toutes les sources Python. Ce
parcours réel a également détecté puis éliminé une combinaison contradictoire
`wx.EXPAND` / alignement dans un `BoxSizer`, devenue bloquante avec wxPython 4.3.

### Sauvegardes successives du profil d'affichage (`tools/tw121_display_profile.py`)

Le test `test_sequential_backups_do_not_overwrite_each_other` échouait par
intermittence sous Windows : deux applications rapprochées lisaient le même
horodatage (résolution d'horloge de l'ordre de la milliseconde), produisaient
le même nom et `shutil.copy2` écrasait la première sauvegarde, c'est-à-dire le
profil d'origine. Le nom est désormais réservé en création exclusive avec un
suffixe `-2`, `-3`… en cas de collision ; le format `Customize.ini.tw121-<horodatage>.bak`
reste inchangé pour la première sauvegarde.

## Cohérence du dashboard sombre

La recette Windows de la version `0.9.1` a révélé deux défauts du composant
d'accueil moderne : le dernier bouton de navigation pouvait absorber toute la
largeur disponible et le fond libre du gestionnaire AUI conservait le gris
natif Windows au milieu de surfaces sombres. Ces anomalies sont propres à la
modernisation UI/UX, pas au socle Vanilla.

La navigation principale utilise désormais un contrôle compact peint avec les
tokens sémantiques, indépendant du chrome natif des `ToggleButton`. Le fond,
les séparateurs, les bordures et les poignées AUI sont raccordés à la même
palette centrale. Le correctif reste transversal au dashboard et ne modifie
aucune couleur de contenu personnalisée par l'utilisateur dans un gadget.

L'icône Windows abandonne le visuel générique Python/disquette et l'ancien
rond bleu. Elle reprend le monogramme `TW`, la mention `CCNS` et les couleurs
publiques de pelemele.org : orange `#FFBD59`, bleu ardoise `#314666` et bleu
profond `#044576`. La même source multi-résolution est utilisée par la fenêtre,
l'exécutable PyInstaller, les raccourcis et l'installateur Inno Setup.

## Fond d’accueil personnalisable — principe retenu

Teamworks devra pouvoir reprendre le principe transversal défini dans `PMSL-Arch/docs/DESIGN_SYSTEM.md` pour les applications desktop.

Cette fonction est **cosmétique et locale** ; elle ne doit pas modifier le métier, le thème global ni les données RH.

Cadrage retenu :

- choix entre fond Teamworks d’origine, éventuels fonds intégrés, `Aucun` et `Image personnalisée…` ;
- image personnalisée stockée comme préférence locale utilisateur/poste, pas comme donnée partagée dans la base ;
- curseur d’**atténuation / intensité** pour casser les grandes surfaces blanches ou adapter le confort visuel ;
- pas de vraie transparence de fenêtre : utiliser un voile ou un mélange appliqué au fond pour rester robuste sous Windows/wxPython ;
- si le fichier choisi est manquant ou illisible, retour automatique au fond d’origine ;
- bouton explicite **Réinitialiser / Rétablir le fond d’origine** ;
- aucune image personnelle ne doit être intégrée automatiquement à un paquet, une release ou une synchronisation ;
- le réglage doit rester indépendant des thèmes Clair / Sombre / Système et ne jamais dégrader les contrastes fonctionnels des contrôles.

**Statut : cadré, non implémenté.** À intégrer après la première recette exploitable, sauf opportunité technique à très faible risque.

## Références

- `docs/CHARTE_GRAPHIQUE_TEAMWORKS.md`
- `docs/33-modernisation-optimisation-sobriete-teamworks-ccns.md`
- `PMSL-Arch/docs/DESIGN_SYSTEM.md`
- `AGENTS.md`
- chantier TW-189 et garde-fous associés


## 29 octobre 2026 — Qt, lisibilité de la fiche individuelle

Sur la copie de production affichant les huit rubriques, la barre Qt native les tronquait et n'offrait que des flèches de défilement minuscules. La navigation conserve le QTabWidget et ses huit pages pour préserver les contrôleurs, mais les expose sur **deux lignes de quatre boutons** accessibles (texte intégral, état sélectionné, clic et suivi des changements de page). Vérification demandée à 900 × 620 et 1380 × 860 via QTest. L'en-tête de fiche et son avatar sont plus compacts, le bandeau de prototype est supprimé, la liste garde une largeur adaptée. Cette évolution concerne uniquement Qt ; aucune requête SQL ni règle métier n'est modifiée.

La barre verticale des individus est remplacée par des commandes nommées « Ajouter » et « Modifier », une recherche pleine largeur et un menu « Autres » présentant explicitement les fonctions indisponibles. La navigation passe à deux colonnes sur une fenêtre étroite pour respecter la largeur réelle des intitulés ; cliquer de nouveau la rubrique active ne la désélectionne plus. Les tests vérifient ces contraintes sans accès à une base réelle.
