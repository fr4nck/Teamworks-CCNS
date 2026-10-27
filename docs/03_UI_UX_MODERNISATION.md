# Teamworks — suivi UI/UX / thème graphique

**Mise à jour : 27 octobre 2026**

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

## Calendrier partagé — proportions et libellés (2026-10-10)

- Provenance : UI/UX. L’écrasement des jours vient de la coque modernisée, pas du métier Présences.
- Mesure Windows native, mois de six semaines, gadget 220 × 180 : dessin historique 208 × 113 et cases 27,71 × 11 ; coque moderne 170 × 44 et cases 22,29 × 0,33.
- Choix utilisateur : proposition G, calendrier d’accueil 320 × 280 ; autres gadgets inchangés. Les tailles persistées plus grandes sont conservées, les tailles trop petites et les anciennes perspectives AUI sont bornées au minimum du calendrier.
- Rétablissement d’une ligne mois/année/flèches et des bordures explicites historiques, avec mise à l’échelle. Palette et callbacks conservés.
- Les noms des jours réservent leur hauteur de texte réellement mesurée et un espace avant les cases pour éviter le recouvrement à différents DPI.
- Qualification locale Windows : Python 3.11.9 / wxPython 4.3.1, 39 tests ciblés passés ; contrôle natif du format G, accueil et restauration d’une ancienne perspective : SUCCESS. À 120 % : gadget 384 × 336, cases 50,86 × 31,83 après restauration, espace texte/cases de 2 pixels. Captures contrôlées dans artifacts/calendar-g-native/. CI du commit exact à contre-valider après push. Aucun merge entre rails, aucune modification de gate Qt.

## Absorption 442 - changement de dossier

Premier lot cible de la branche fix/rc2-ui-state-context-refresh-20260919 :
invalidation des caches et selections de l'ancien dossier, notification des
pages et rechargement du contenu des gadgets sans reconstruire les panes AUI.

Les protections de taille du calendrier et le rendu groupe de Personnes
sont conserves. Au terme de ce premier lot, la persistance generique des
tableaux restait a integrer ; elle est absorbee par le second lot ci-dessous.

Qualification locale Windows : tests de contexte, cache, gadgets, layout,
comportement des selections, smoke natif Personnes et verification native
du calendrier G reussis. Aucun schema ni aucune base metier modifies par
l'absorption. La recette utilisateur du changement de dossier reste a faire.

## Absorption 442 - persistance du tableau Personnes

Second lot cible de fix/rc2-ui-state-context-refresh-20260919 : etat versionne
par vue pour les vues core dans Customize.ini (ui_views), largeur et ordre des colonnes, choix
visibles/masques. Les colonnes ne sont plus reconstruites a chaque MAJ des donnees.
La vue Personnes moderne conserve son stockage Config.json existant, sa
sauvegarde du tri et ses largeurs par defaut (telephone 200, qualifications 90).
Le view_id generique y est retire avant construction : aucune seconde source
de preferences ne peut ecraser les choix existants ni leur reinitialisation.
Les parametres sont propres a chaque instance ; les defaults globaux ne sont
pas modifies par une personnalisation. Un etat invalide revient aux defaults.
Le tri initial par nom est resolu par sa cle stable meme si la colonne a change
de position. Le rendu groupe Freeze/Thaw et l'invalidation du dossier du premier
lot sont conserves. Aucun changement du calendrier, du rail Qt ou des gates.

Provenance : UI/UX du fork moderne (persistance des preferences utilisateur),
aucune modification du schema ni des bases metier, aucun backport Vanilla.
Qualification locale : tests de normalisation/etats/layouts et smokes natifs de
l'application ; controle wx reel du rafraichissement, fermeture/reouverture,
largeurs, ordre, colonnes masquees et isolation entre instances, preferences
et donnees synthetiques isolees. Ce controle n'ecrit pas la configuration usuelle.

La persistance du tableau precedemment indiquee comme restante est absorbee
par ce second lot. Recette utilisateur restante : sur une copie de base,
changer de dossier, verifier selections/filtres/gadgets et retrouver les
preferences de colonnes apres redemarrage.

Etat GitHub reverifie le 12 octobre 2026 : la PR #442 est fermee sans fusion
depuis le 11 octobre ; sa branche distante n'existe plus. Ce chantier n'a
supprime aucune branche. Le sommet historique `5712aa019c557736045b05a214af41b11f579f77`
reste accessible via `refs/pull/442/head` pour reprendre l'audit des autres
fichiers. Les deux lots absorbes ne prouvent pas l'integration de tous les
changements de cette PR. Ne pas rejouer le sommet en bloc :
`UTILS_Etat_vues.py` contient deja des gardes supplementaires sur `wx/master`
(types de collections et `OverflowError`) absentes de la source historique.

## Recette Windows Vanilla wx 0.9.2 RC3 (2026-10-13)

Les constats certains de la vidéo de recette ont été corrigés dans leur portée
propre :

- l'assistant de démarrage utilisait une image historique de 136 × 24 contenant
  déjà le mot « Fermer » comme si elle était une icône carrée du bouton commun ;
  l'action utilise désormais le libellé natif, l'icône carrée existante et le
  focus clavier du contrôle commun ;
- les cinq commandes de choix du document de publipostage ne forment plus une
  colonne latérale contrainte : elles se redistribuent sous la liste et gardent
  leur largeur naturelle ;
- « Point de départ » et « Caractéristiques générales » constituent une seule
  étape logique. Les deux validations sont exécutées dans l'ordre et la
  navigation saute une action « Suivant » sans changer les données produites ;
- les couples libellé/contrôle des préférences sont empilés et le réglage long
  de l'adresse de rapport se redistribue verticalement dans le corps défilant ;
- l'en-tête de la fiche individuelle est rafraîchi après l'import de l'identité
  et couvre les cas nom seul, prénom seul et nom avec prénom.

La densité de l'onglet Généralités reste régie par les métriques communes et le
correctif `b1aafb05`. Les groupes Identité, Adresse, Coordonnées et Mémo gardent
leur séparation sémantique ; aucune marge locale supplémentaire n'a été ajoutée.
Les états transitoires entrevus dans Présences et dans les données de contrat
n'ont entraîné aucune modification faute de reproduction.

La qualification automatisée couvre les contrats de disposition, la navigation
fusionnée, le formatage de l'en-tête, les garde-fous de densité, le thème, le DPI
et la compatibilité wx. Elle ne remplace pas une recette visuelle Windows aux
échelles réelles ; aucune validation visuelle DPI n'est revendiquée pour ce lot.

## CI Windows RC4 — réalignement des parcours critiques (2026-10-14)

Le job « Parcours critiques Windows » échouait depuis `5267043b` puis sur
`0f126db2` (run 38369194970). Trois smokes décrivaient encore la structure
antérieure de l'interface :

- **modèle de contrat** : `ListCtrl_champs` lit désormais `dictChamps` sur sa
  fenêtre de premier niveau (`5267043b`). Les deux smokes de checklists
  plaçaient ce dictionnaire sur un panneau intermédiaire ; ils construisent
  maintenant un `wx.Dialog` de contexte avec la StaticBox réelle ;
- **assistant contrat** : depuis l'étape fusionnée RC3, la page 3 n'est jamais
  atteinte seule. Les smokes appuyaient une seconde fois sur « Suivant » avant
  de renseigner les caractéristiques : la validation conjointe ouvrait une boîte
  modale et le smoke expirait après 180 s. Trois smokes sont réalignés, dont
  `smoke_pmsl_contracts_21h.py`, qui n'est pas exécuté par la CI. Ce dernier
  expire encore plus loin, sur une boîte modale de validation du premier CDD :
  il reste non qualifié ;
- **fiche individuelle** : le seuil absolu `hauteur adresse >= 50 px` venait de
  l'ancien minimum fixe de 72 px. ADR-005 (`b1aafb05`) fixe deux lignes
  visibles, soit 42 px à 100 % sous Windows. Le smoke vérifie désormais que le
  champ ne descend pas sous son minimum sémantique ni sous deux lignes de texte.

Une régression fonctionnelle de la fusion RC3 est corrigée dans le même lot.
Le modèle choisi n'était appliqué qu'au clic sur « Suivant » : les
caractéristiques affichées sur le même écran n'étaient pas pré-remplies, puis
la saisie de l'utilisateur était écrasée sans avertissement. Le modèle est
maintenant appliqué dès sa sélection. « Suivant » ne le réapplique que si la
sélection a changé depuis, ou si la liste des modèles a été rechargée.
L'affirmation RC3 « sans changer les données produites » ne valait donc pas
pour le parcours avec modèle.

Garde-fou : `tests/test_rc4_windows_smoke_alignment.py` vérifie que les étapes
attendues par les smokes contrat sont atteignables, que la liste d'onglets du
smoke fiche correspond à `DLG_Fiche_individuelle_lazy`, le contexte de premier
niveau des smokes de checklists et la non-réapplication du modèle.

## Recette Windows RC4 — surbrillance instable des contrats (27 octobre 2026)

**Statut : défaut visuel signalé, observé sur vidéo, cause non encore confirmée ; aucun correctif livré.**

Dans la version `0.9.2-rc4` sous Windows 11, lors du déplacement du pointeur
sur les lignes de l'onglet **Contrats** d'une fiche individuelle, une bande
bleue pâle suit le pointeur et change rapidement de ligne tandis que la
ligne sélectionnée conserve son surlignage. La vidéo de recette de 11,8 s
montre ce phénomène notamment entre 3,5 et 4,3 s ; le reste de la fenêtre
demeure stable, sans rechargement général visible.

**Confidentialité :** la vidéo contient des informations personnelles ;
ne pas la joindre au dépôt public ni reprendre d'identité ou de contrat
réel dans la documentation.

**Point d'entrée du code :** `teamworks/Ctrl/CTRL_Page_contrats_core.py`,
classe `ListCtrl_contrats`, liste `wx.ListCtrl` avec `LC_REPORT`,
`LC_HRULES`, `LC_VRULES` et `LC_SINGLE_SEL`. Cette classe ne lie pas
`EVT_MOTION` : un effet de survol natif Windows et/ou une interaction avec
les séparateurs est une **hypothèse**, et non un diagnostic confirmé.
L'ajustement des colonnes est différé lors de `EVT_SIZE` : rechercher
d'éventuels déclenchements répétés seulement si les traces le justifient.

**Qualification ciblée à effectuer :**

1. Reproduire avec plusieurs contrats, sélectionner une ligne, puis
   déplacer lentement la souris sur les autres sans cliquer ; comparer
   avec la souris immobile.
2. Comparer sur une copie de test la liste avec et sans `LC_HRULES` et
   `LC_VRULES` ; distinguer les surbrillances de survol de l'effacement
   réel des traits.
3. Vérifier le double buffering natif déjà fourni par wxWidgets avant
   d'envisager une correction de peinture.
4. Vérifier sélection, double-clic, clavier, menu contextuel et les
   échelles Windows 100 %/125 % après toute correction.
5. Ratisser les autres listes uniquement si la cause générique est
   confirmée, puis publier dans un **nouveau jalon** sans réécrire le tag RC4.

Il s'agit d'une anomalie **UI/UX non bloquante métier dans la vidéo**,
mais gênante pour la qualité visuelle. La vidéo ne prouve ni régression
de données ni cause liée à SQL.


## Lot RC5 — boutons de navigation et scintillement contrats (27 octobre 2026)

**Correctifs candidats intégrés à wx/master, validation visuelle Windows encore requise.**

- **Retour/Suivant du publiposteur :** les images historiques
  `BoutonsImages/*_L72.png` mesurent **72 × 24 pixels** et contiennent déjà
  un libellé. La RC4 les compressait dans une icône de 22 × 22 pixels puis
  dessinait une seconde fois le texte natif du bouton. Les actions utilisent
  désormais de vraies icônes `Images/32x32`, affichées à 18 × 18 et
  séparées du texte. `SetSuiteAction` conserve les transitions Suivant,
  Valider, Arrêter et Fermer, mais remplace leurs anciens visuels 72 × 24.
  Le bouton commun ne compacte plus un sprite `*_L72.png` lorsqu'il
  possède déjà un libellé natif.
- **Scintillement des listes contrats :** sur Windows, la liste native
  `wx.ListCtrl` n'utilise plus `LC_HRULES` et `LC_VRULES`, impliqués
  dans un bug connu de wxWidgets sous Windows au survol ; le mode Report
  et la sélection unique restent inchangés. Les règles sont conservées sur
  les autres plateformes. `Remplissage` regroupe les opérations via
  `Freeze/Thaw` et le redimensionnement évite les écritures identiques
  de largeur de colonnes. Pas de modification SQL ni de contrat.
- **Classification CEE :** reprendre les correctifs précédents déjà
  qualifiés pour `CLASSIFICATION` et les trois libellés contractuels,
  sans changer les codes métier ou les données des contrats.

**Contrôles automatiques :** tests du mapping des icônes, exclusion des
sprites larges, style natif de la liste selon la plateforme, mises à jour
groupées et validation des boutons dans le smoke de publipostage Windows.

**Recette manuelle restant obligatoire :** captures Windows du publiposteur
à 100 % et 125 %, navigation Suivant/Retour/Valider/Arrêter/Fermer et
survol de plusieurs lignes de contrats, puis édition Word d'un CEE sur
copie de base. Le tag RC4 publié n'est pas réécrit.
