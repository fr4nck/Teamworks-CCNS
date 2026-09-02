# Teamworks-CCNS 0.9.1e — Généralités, adresses et lieux

## But

La 0.9.1e reste une corrective/UX. Elle doit rendre la fiche Généralités exploitable sans fenêtre « chewing-gum », sans blocage franco-français et sans dépendance réseau obligatoire.

## Généralités

- « Adresse postale » contient l’adresse complète, le code postal et la ville.
- « Téléphones et e-mails » est édité directement dans Généralités.
- `DLG_Saisie_coords` ne doit plus être invoqué depuis Généralités. Il reste temporairement disponible pour les écrans historiques qui en dépendent encore ; suppression définitive après migration de tous ses consommateurs.
- Les champs utilisent les rôles sémantiques de `UTILS_Styles` afin que leur largeur soit cohérente avec leur contenu.

## Mise en page responsive / Windows 11 Snap

La fiche ne doit pas supposer que Teamworks-CCNS occupe tout l’écran. Le cas d’usage de référence inclut explicitement une fenêtre ancrée sur une moitié d’écran avec, à côté, Noethys, un navigateur ou un PDF servant de source de saisie.

- Le nombre de colonnes dépend de la largeur réellement disponible dans la fenêtre, pas de la résolution totale de l’écran.
- Le calcul utilise une largeur logique corrigée de l’échelle d’interface : un écran très large à 200–220 % peut nécessiter une disposition plus compacte qu’à 100 %.
- À largeur confortable : conserver une composition en deux colonnes lisible.
- À largeur réduite : empiler les sections sur une seule colonne au lieu de comprimer les champs ou tronquer les libellés.
- Le changement de disposition doit suivre `EVT_SIZE` et fonctionner pendant un Snap/unsnap Windows 11 sans redémarrer la fiche.
- Les formulaires étroits doivent devenir défilables verticalement si leur hauteur dépasse la zone de travail ; aucune donnée ne doit être inaccessible.
- Les champs extensibles (adresse, e-mail, texte long) utilisent l’espace supplémentaire ; les champs courts (date, CP, téléphone, NIR) restent bornés à leur contenu utile.
- Les boutons d’action doivent se regrouper/revenir à la ligne plutôt que créer une largeur minimale artificielle.

Le seuil de bascule doit être exprimé en largeur logique et centralisé, afin d’éviter des valeurs différentes dans chaque écran. Le comportement visé est notamment : demi-écran ultrawide à 100 % = deux colonnes si l’espace le permet ; demi-écran standard ou fort zoom = une colonne propre.

## Icônes

Les icônes font partie du contrat responsive : elles ne doivent ni rester minuscules lorsque le texte est agrandi, ni devenir floues parce qu’une source 16x16 est étirée artificiellement.

- Les tailles d’icônes restent sémantiques et centralisées (`micro`, `small`, `medium`, `large`, `hero`) au lieu d’être décidées écran par écran.
- La taille affichée suit l’échelle d’interface exactement comme le texte et les contrôles.
- Pour les anciens PNG, le moteur choisit automatiquement la meilleure variante disponible parmi 16, 22, 32, 48, 80 et 128 px avant redimensionnement final.
- Les boutons d’action utilisent par défaut la taille sémantique `medium`; les barres d’outils et navigations conservent des rôles plus généreux lorsqu’ils existent.
- Une icône seule doit conserver une cible cliquable cohérente avec la hauteur minimale du contrôle ; on ne doit pas obtenir une minuscule cible juste parce que le pictogramme est petit.
- Le zoom 200 % et les futurs zooms supérieurs doivent augmenter l’icône, ses marges et sa cible d’interaction sans doubler l’échelle.
- La migration vers une famille d’icônes cohérente (Fluent System Icons selon le design system) reste progressive : la 0.9.1e corrige d’abord dimensionnement, netteté et cohérence des ressources existantes sans casser les écrans historiques.

## Lieux et codes postaux

### Naissance

- France : recherche/contrôle assisté français.
- Hors France : ville libre, code postal facultatif et non limité au format français ; aucune erreur parce qu’un lieu n’existe pas dans `Villes.db3`.
- Le pays de naissance pilote explicitement cette politique.

### Résidence

- L’adresse complète doit être persistée et réaffichée avec le code postal et la ville.
- Une ville ou un code postal inconnu de la base française n’est jamais bloquant.
- Le format du code postal doit pouvoir accueillir les formats européens et ne plus être un masque `#####` universel.

## Recherche assistée

Le logiciel doit fonctionner hors ligne et accepter une saisie libre. La recherche n’est qu’une aide.

- France : COG Insee pour communes/pays et service de géocodage de la Géoplateforme pour les adresses françaises. L’ancienne API Adresse BAN est dépréciée.
- International : utiliser un fournisseur abstrait et remplaçable. GeoNames est le candidat privilégié pour les villes ; ses données sont disponibles en CC BY 4.0 et `cities500.zip` couvre environ 185 000 villes/sièges administratifs. Une base SQLite locale Europe peut être générée au build pour éviter une dépendance réseau permanente.
- Ne pas utiliser l’API publique Nominatim comme autocomplétion : sa politique l’interdit. Si un fournisseur OSM est utilisé un jour, il devra être explicitement configurable et conforme à sa politique.
- Toute recherche réseau se déclenche par action utilisateur (« Rechercher »), avec cache local ; jamais une requête à chaque caractère.

## Géométrie et zoom

- Formulaire court : profil `fit`.
- Ordre impératif : appliquer thème/polices/DPI/zoom, recalculer les tailles préférées, puis `Layout()` + `Fit()`.
- Contenu dynamique : `RefitWindow()` après modification.
- Si le contenu excède la zone de travail : borner la fenêtre à l’écran et rendre le contenu défilable ; ne jamais rogner le texte.

## Recette minimale

- Luxembourg / Luxembourg accepté comme lieu de naissance.
- Belgique / Bruxelles accepté.
- Un code postal étranger alphanumérique peut être conservé.
- L’adresse complète est enregistrée puis réouverte à l’identique.
- Une fiche peut être créée et enregistrée sans connexion Internet.
- Le mode France conserve sa recherche assistée.
- Les fenêtres `fit` ne rognent pas les contrôles après application du zoom/thème.
- Les champs date, CP, ville, téléphone, e-mail et adresse ont des dimensions sémantiques cohérentes.
- Snap Windows 11 sur demi-écran ultrawide : fiche exploitable et équilibrée sans grands vides ni champs écrasés.
- Snap sur demi-écran standard : bascule automatique en une colonne et défilement vertical propre.
- Zoom fort (200 % et comportement prêt pour 220 %) : la décision une/deux colonnes tient compte de la largeur logique et aucun texte n’est tronqué.
- Les icônes grandissent avec le zoom et restent nettes en sélectionnant une ressource source suffisamment grande.
- Les boutons à icône seule conservent une cible cliquable cohérente avec la hauteur minimale des contrôles.

La refonte structurante contrats/temps de travail reste ciblée 0.9.2.