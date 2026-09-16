# Core documentaire PMSL / Teamworks — première itération

Date : 2026-09-16  
Base : `qt/convergence-0.9.2-rc3` — `4ed3c4b1831781454e8bd82ce0501788f91a9668`  
Statut : prototype parallèle ; aucune substitution de la Vanilla wx.

## Référentiel PMSL-Arch consulté

Avant le code : `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLITIQUE_DEVELOPPEMENT.md`, `docs/GOUVERNANCE_DOCUMENTAIRE.md`, ADR-001, ADR-008, ADR-011 et `docs/IMPLEMENTATION_CONTRATS_INTERAPPLICATIONS.md`.

Conséquences appliquées : Teamworks-CCNS reste source de vérité RH/emploi ; le moteur documentaire n'est pas une base métier parallèle ; aucun accès direct à une base Dolibarr ; aucun contrat wx/Qt/SQL dans le core ; vocabulaire métier `SALARIE_*` / `CONTRAT_*` ; aucune API réseau, microservice ou GED créée. La conservation, l'original et la copie restent gouvernés par PMSL-Arch.

L'identité `STRUCTURE_*` existe déjà dans le contexte actuel, mais son extension au registre transverse devra rester alignée avec PMSL-Arch et ne doit pas devenir une nouvelle règle locale Teamworks.

## Audit legacy

Rail de convergence déjà présent et réutilisé :

```text
UTILS_Publipostage_donnees
        -> UTILS_Documents_RH
        -> application.services.hr_documents
        -> domain.documents.MergeContext
```

`UTILS_Publipostage_donnees.py` mêle accès SQL direct, formatage, vocabulaire historique et dépendance wx : il reste adaptateur legacy et n'est pas importé par le core.

`UTILS_Documents_RH.py` est déjà un pont utile : il lit les valeurs historiques, les projette en salarié/contrat, appelle `prepare_hr_document()` et conserve les mots-clés historiques dans `extra`. Il reste côté adaptateur Teamworks.

`application/services/hr_documents.py` orchestre type documentaire, `MergeContext` et champs requis. `domain/documents` existait déjà au HEAD qualifié avec catalogue et contexte : cette itération l'étend au lieu de créer un second core concurrent.

`DLG_Publiposteur.py` mélange UI wx, globals (`DICT_DONNEES`), champs personnalisés DB et choix des moteurs/canaux. `DLG_Publiposteur_contrat.py` reste également une couche de compatibilité wx/DB.

`DLG_Teamword.py` mélange UI, données, modèle et rendu ; la fusion HTML historique observée repose encore sur des remplacements de chaînes (`texteHtml.replace(...)`).

`CTRL_Editeur_email.py` dépend directement de `wx.richtext` pour saisie riche, lecture/écriture TWD/HTML/RTF, aperçu et impression (`RichTextPrinting`). Le nouveau core coupe cette dépendance.

Le TWD/XML historique reste une source à lire, jamais à écraser. Cette itération fournit l'étape pure après lecture legacy : conversion des `{MOTSCLES}` connus en champs sémantiques. Le lecteur wx RichText XML/TWD complet reste à encapsuler dans `legacy/` ; il ne sera pas requis par le fonctionnement normal du core.

## Architecture minimale

```text
PMSL-Arch
   -> règles transverses
       -> domain.documents
          -> DocumentModel
          -> MergeFieldRegistry
          -> HtmlMergeRenderer
       <- application/services
       <- adaptateurs Teamworks RH / legacy
       <- base Teamworks actuelle
```

À côté, la Vanilla wx/Teamword reste en production. Le POC Qt consomme `domain.documents`. Le core n'importe ni wx ni PySide/PyQt.

## Contrats ajoutés

`DocumentModel` v1 apporte UUID, `format_version`, type, HTML, métadonnées, assets et options de rendu JSON-compatibles. `Asset` utilise `asset://UUID`, contenu base64 dans ce prototype et SHA-256. Une version inconnue est refusée explicitement.

`MergeFieldRegistry` porte clé canonique, libellé, domaine propriétaire, source de vérité actuelle, catégorie, type, contextes, alias, tokens historiques, statut et `resolver_id`. La première série couvre les champs salarié/contrat déjà projetés par l'adaptateur : identité, coordonnées, dates, type, classification, convention, groupe CCNS, durée hebdomadaire et salaire brut mensuel.

`HtmlMergeRenderer` reçoit uniquement `DocumentModel + MergeContext -> RenderResult`. Il nettoie le HTML, résout les `span[data-pmsl-field]`, échappe les valeurs, rend visibles les champs manquants et propose un mode strict. Un champ absent du registre ne peut pas être résolu par simple collision de nom dans le contexte.

Le sanitizer autorise un sous-ensemble HTML documentaire (paragraphes, styles simples, listes, tableaux, liens sûrs, images `asset://`, sauts de page) et supprime contenu actif, événements JavaScript, protocoles dangereux, images réseau implicites et CSS à URL/expression.

Détail du format : `docs/DOCUMENT_FORMAT_V1.md`.

## Prototype Qt

`poc/qt-theme/document_editor_demo.py` utilise le PySide6 déjà présent dans le rail POC Qt. Fonctions : nouveau document, saisie riche, gras/italique, insertion d'un champ métier, sauvegarde JSON, réouverture, `MergeContext` fictif et aperçu fusionné.

Le POC projette temporairement un champ canonique en lien interne `pmsl-field:SALARIE_NOM` pour `QTextEdit`, puis le reconvertit à la sauvegarde en `<span data-pmsl-field="SALARIE_NOM">...</span>`. `DocumentModel` ne connaît pas `QTextEdit`.

L'environnement local de cette itération ne disposait pas de PySide6 : les fonctions d'adaptation sont testées sans Qt et le smoke runtime `QTextEdit` est automatiquement ignoré localement. La CI Qt du dépôt installe déjà PySide6.

## Technologie éditeur

Qt natif / `QTextEdit` est retenu uniquement pour ce POC : dépendance déjà présente, offline, pas de nouvelle pile JS, delta minimal. Il faudra valider tableaux, collage Word/LibreOffice, images, sauts de page, fidélité impression et véritable atomicité des variables avant d'en faire le choix final.

Si le natif atteint ses limites : Tiptap/ProseMirror est le candidat web principal (schéma et nœuds personnalisés adaptés aux variables atomiques) ; Quill reste candidat secondaire. Tout composant web devra être embarqué localement et isolé derrière un adaptateur. Le format métier ne sera ni un Delta Quill ni un schéma propriétaire de l'éditeur.

Licences à auditer avant distribution : PySide6/Qt selon licence/composants/distribution ; Tiptap OSS MIT ; Quill BSD-3-Clause ; CKEditor 5 open source GPL 2+ avec offre commerciale séparée. Le legacy inspecté contient également des en-têtes GNU GPL. Cette note n'est pas un avis juridique.

## Veto architectural

- `DocumentModel` : nécessaire pour sortir le document du widget ; coût = migrations de format à gérer ; réversible par contrat versionné.
- `MergeFieldRegistry` : nécessaire pour sortir les mots-clés des chaînes anonymes ; coût = discipline d'enregistrement ; réversible car structures simples.
- `HtmlMergeRenderer` : nécessaire pour sortir la fusion de wx et de `str.replace`; coût = sous-ensemble HTML à maintenir ; remplaçable derrière `RenderResult`.
- `Asset` : nécessaire pour ne pas figer des chemins Windows ; le stockage base64 est provisoire, pas une GED.
- API/microservice/adaptateur Dolibarr : aucun besoin actuel ; non développés.

## Portabilité et Dolibarr

Le test de portabilité lance un nouveau processus Python et interdit explicitement les imports `wx`, `PySide6`, `PyQt5`, `PyQt6`; il importe ensuite `domain.documents`, sérialise un document, crée un contexte depuis un mapping simple et effectue la fusion.

C'est suffisant pour démontrer aujourd'hui qu'un futur consommateur peut fournir des données neutres sans accès direct à la base Teamworks. Aucun code Dolibarr n'est ajouté. Une future génération inter-applications, un registre partagé ou une synchronisation documentaire nécessiteront un contrat/ADR PMSL-Arch. Salarié, contrat, CCNS et temps de travail restent propriété RH tant que PMSL-Arch n'en décide pas autrement.

## Tests

Résultat local : `25 passed, 1 skipped`. Le skip est uniquement le smoke runtime `QTextEdit` faute de PySide6 local. `python -m compileall -q domain tests poc/qt-theme` est vert.

Couverture : modèle, JSON, version, assets/hash, registre/provenance/collisions, contexte neutre, compatibilité du builder existant, fusion/échappement, champs manquants/inconnus, mode strict, sanitizer, protocoles/images, placeholders legacy, projection Qt et portabilité sans wx/Qt.

Corpus A-G : A texte simple ; B gras/italique/couleur/alignement ; C image `asset://` ; D lien ; E mots-clés ; F structure de saut de page ; G tableau + mise en forme + champ. La pagination physique et la comparaison pixel à pixel avec wx ne sont pas encore couvertes.

## Risques et prochaines petites étapes

1. Constituer de vraies fixtures TWD/XML A-G et encapsuler le lecteur wx dans une couche legacy stricte.
2. Importer les bitmaps TWD vers `Asset` sans casser la source.
3. Tester le POC Qt sur Windows avec collage Word/LibreOffice, tableaux et champs atomiques.
4. Ajouter un renderer PDF/print partant de `DocumentModel`, jamais du widget.
5. Ajouter ensuite un `EmailRenderer` si le format commun est stabilisé.
6. Étendre le registre progressivement, en renvoyant à PMSL-Arch toute règle transverse.

Non fait : aucune modification de la Vanilla wx, aucun remplacement de Teamword, aucune migration automatique, aucune API réseau, aucun module Dolibarr, aucune base documentaire dédiée, aucun renderer PDF/email de production.
