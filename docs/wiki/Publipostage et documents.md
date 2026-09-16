# Publipostage et documents

Teamworks-CCNS possède un **assistant commun d’édition de documents**. Il ne se limite pas à Word et Writer : il sait aussi créer et fusionner des modèles avec **Teamword, le traitement de texte intégré**.

## Où lancer le publipostage ?

Un parcours confirmé est la liste **Individus** : sélectionnez la ou les personnes puis utilisez le bouton **courrier** (« créer un courrier ou un Email par publipostage »). Les contrats, candidats et candidatures possèdent aussi des contextes de données dans le moteur de publipostage.

## Les six étapes de l’assistant

1. **Introduction** — rappelle le principe des modèles et des balises `{NOM}`.
2. **Vérification des données** — grille des mots-clés et valeurs pour chaque document ; les cellules peuvent être corrigées avant fusion. On peut imprimer la liste au format PDF et gérer des champs personnalisés.
3. **Choix du logiciel** — Microsoft Word, Writer, traitement de texte intégré Teamword ou éditeur Email Teamword.
4. **Choix du modèle** — sélectionner, importer, actualiser, créer, modifier ou supprimer un modèle.
5. **Options d’édition** — impression, nombre d’exemplaires, imprimante, sauvegarde, dossier/nom/préfixe, aperçu ; le mode Email affiche ses paramètres dédiés.
6. **Exécution** — création de chaque document, remplacement, sauvegarde/impression/aperçu/envoi selon les options puis compte rendu de progression.

## Choisir le bon éditeur

### Teamword — éditeur interne

Choisissez **Traitement de texte intégré** pour rester dans Teamworks. Les modèles sont des fichiers `.twd`; la liste des mots-clés est affichée dans un panneau et un double-clic insère la balise. Voir [[Éditeur interne et documents]].

### Microsoft Word

La voie Word utilise l’automatisation Microsoft Word et des modèles `.doc`. Sur Windows, Word doit être réellement installé et accessible à l’automatisation COM. La création d’un nouveau modèle ouvre Word et insère un texte d’exemple avec la liste des mots-clés du contexte.

### Writer (LibreOffice/OpenOffice selon l’installation)

L’interface conserve le libellé historique **OpenOffice Writer** et utilise des modèles `.odt`. Le moteur Linux passe par UNO/`soffice`; le code possède aussi une classe Writer Windows. Le wiki parle donc de Writer sans inventer une intégration « LibreOffice moderne » séparée : la compatibilité dépend de l’installation UNO/soffice disponible sur le poste.

### Email intégré

Le quatrième choix utilise Teamword comme éditeur HTML de mail. Le destinataire est alimenté par la valeur `{EMAILS}` du document courant. Les paramètres d’expédition, sujet et pièces jointes sont saisis dans l’assistant.

## Modèles

Les modèles sont regroupés dans le répertoire retourné par Teamworks pour les modèles (`UTILS_Fichiers.GetRepModeles()`). L’assistant filtre selon le moteur choisi : `.doc`, `.odt` ou `.twd`.

**Importer** copie un modèle existant dans ce répertoire et refuse un doublon de même nom. **Ajouter** crée un nouveau modèle dans l’éditeur choisi. **Modifier** ouvre le modèle sélectionné. **Supprimer** efface le fichier après confirmation.

## Mots-clés et vérification avant fusion

La syntaxe est `{MOTCLE}`. L’étape 2 est le meilleur endroit pour vérifier ce que le contexte expose réellement :

- [`{CIVILITE}`](Mots-clés-de-publipostage#publipostage-civilite)
- [`{NOM}`](Mots-clés-de-publipostage#publipostage-nom)
- [`{PRENOM}`](Mots-clés-de-publipostage#publipostage-prenom)
- [`{DATENAISS}`](Mots-clés-de-publipostage#publipostage-datenaiss)
- [`{ADRESSERESID}`](Mots-clés-de-publipostage#publipostage-adresseresid)
- [`{CPRESID}`](Mots-clés-de-publipostage#publipostage-cpresid)
- [`{VILLERESID}`](Mots-clés-de-publipostage#publipostage-villeresid)
- [`{TELEPHONES}`](Mots-clés-de-publipostage#publipostage-telephones)
- [`{EMAILS}`](Mots-clés-de-publipostage#publipostage-emails)

Pour les contrats, voir aussi [`{DATEDEBUT}`](Mots-clés-de-publipostage#publipostage-datedebut), [`{TYPECONTRAT}`](Mots-clés-de-publipostage#publipostage-typecontrat) et [`{SALAIREBRUTMENSUEL}`](Mots-clés-de-publipostage#publipostage-salairebrutmensuel).

Référence complète : [[Mots-clés de publipostage]].

## Champs personnalisés

L’assistant peut ajouter des champs personnalisés à une catégorie de publipostage. Ils reçoivent un nom de mot-clé et une valeur par défaut puis apparaissent dans la grille ; ils sont marqués `*` dans la liste imprimée. Les contrats peuvent en outre exposer les mots-clés définis dans `contrats_champs`.

## Valeurs absentes

Une donnée connue mais absente est généralement fusionnée en chaîne vide. Une balise non connue du contexte n’est pas automatiquement devinée : elle peut rester visible dans le document final. Contrôlez donc la grille avant de produire un document officiel.

## Impression, sauvegarde et aperçu

L’assistant sait sélectionner le nombre d’exemplaires et l’imprimante, enregistrer les documents dans un répertoire choisi et proposer un aperçu. Le nom de fichier par défaut est construit à partir d’un préfixe et d’éléments du contexte (nom/prénom/dates selon la catégorie).

## Erreurs fréquentes

- **La balise reste visible** : vérifiez l’orthographe, les accolades, la casse et surtout que le contexte l’expose.
- **Une valeur est vide** : regardez la grille de l’étape 2 avant d’accuser le modèle.
- **Word ne s’ouvre pas** : vérifiez l’installation de Word/COM.
- **Writer ne s’ouvre pas** : vérifiez l’installation UNO/soffice compatible avec la voie choisie.
- **Modèle absent de la liste** : vérifiez son extension pour l’éditeur sélectionné.
- **Champ personnalisé absent** : vérifiez la catégorie de publipostage et le dossier ouvert.
