# Teamworks-CCNS 0.9.2


## Candidate RC10 — 29 octobre 2026 (recette utilisateur Windows requise)

- **Sélecteur de période :** correction de l'exception `AttributeError: ctrl_mois` de RC9 : les événements de la liste s'adressent au dialogue réel (et non au panneau de section), et les contrôles mois, année et dates sont construits avant la liste. La sélection native précoce est couverte par une régression Windows et des tests synthétiques (`d00f417`).
- **Fiche individuelle :** les neuf onglets natifs passent de 20 à 38 px à l'échelle d'interface 100 %, avec centrage vertical amélioré et largeur stabilisée pendant la navigation. Mesure native `TCM_GETITEMRECT` et smoke Windows (`4887bba`).
- **Validation avant packaging :** CI Linux et parcours critiques Windows verts sur `4887bba`, run `40898264166`. La construction du portable et de l'installateur de la RC10 doit être validée sur le commit de version exact.
- **Réserves :** les véritables DPI système Windows 125 % et 150 % n'ont pas été qualifiés ; recette utilisateur sur copie de base requise, notamment pour la sélection des périodes et les écrans métiers. Un échec de test contrat 21 h, déjà observé sur le code antérieur hors de ce périmètre, reste à analyser séparément. Aucun changement des données MySQL ni des règles métier dans ces deux corrections.

## Candidate RC9 — 29 octobre 2026 (recette utilisateur Windows requise)

- **Crash À propos → Licence corrigé :** le paquet Windows portable et l'installateur incluent obligatoirement `Licence.txt` à la racine de l'exécutable. Son contenu est vérifié contre le fichier source avant publication ; le dialogue traite l'absence ou l'illisibilité sans exception Python. Régression constatée sur RC6 `154da83c`.
- **Sauvegardes limitées au contexte Teamworks :** l'écran ne parcourt plus tous les dossiers `_TDATA` du répertoire commun ni les bases `_tdata` du serveur MySQL. Il ne propose que le dossier Teamworks actuellement ouvert et ses composants de base, photos, documents. Les anciens profils automatiques qui demandent un autre dossier sont refusés plutôt qu'exportés silencieusement.
- **Sauvegarde MySQL renforcée :** export par `mysqldump` sans console noire sous Windows, surveillance des blocages, refus des exports échoués ou vides, contrôle de l'archive ZIP avant publication et conservation de l'ancienne sauvegarde en cas de copie interrompue.
- **Fenêtre de sauvegarde :** redimensionnable, arbres plus lisibles et message final précisant ce qui a été effectivement sélectionné.
- **Tests automatisés :** couverture du fichier GPL manquant et présent (UTF-8), du contenu obligatoire des paquets, de la restriction aux bases du dossier actif et de l'intégrité des sauvegardes. CI Linux et Windows entièrement verte sur `77a985e6` avant changement de version.
- **Réserves :** aucun serveur MySQL de production ni archive personnelle n'a été modifié. La conformité du rendu visuel, la navigation souris et la restauration effective d'une archive complète restent à valider sur une copie de base Windows. RC6/RC8 publiées restent intactes.

## Candidate RC8 — 28 octobre 2026 (recette utilisateur Windows requise)

- **Clic direct sur le salarié :** un clic sur le libellé d'une personne dans l'arbre « État des dossiers » ouvre sa fiche ; les clics sur les catégories, les icônes d'expansion et les alertes n'entraînent aucune ouverture involontaire.
- **Alertes actionnables :** double-clic ou Entrée sur une information, une pièce ou un contrat ouvre le parcours ciblé déjà introduit en RC7, avec identifiants exacts, sans recherche manuelle.
- **Onglets à chargement différé :** charger synchroniquement Qualifications ou Contrats avant de lancer la saisie de pièce ou la DPAE ; éviter une action perdue sur un onglet encore vide.
- **Navigation robuste :** ouverture différée hors traitement de souris et protection contre les doubles boîtes de dialogue en cas de clic suivi d'une activation.
- **Sécurité métier :** confirmation explicite avant marquage de la signature et aucune attestation automatique de dépôt DPAE ; recalcul des alertes après fermeture de la fiche.
- **Qualification :** tests synthétiques des clics, de l'activation clavier, des onglets différés et des cibles contractuelles ; CI Linux et Windows vertes sur `ba5f35a5` avant changement de version. Vérification manuelle de la souris et des données réelles encore nécessaire.
- **Exploitation :** aucune base en production modifiée, aucune donnée personnelle de capture publiée et aucun tag RC7 réécrit.


## Candidate RC7 — 27 octobre 2026 (recette utilisateur Windows requise)

- **État des dossiers interactif :** un double-clic (ou la touche Entrée) sur la personne ou une alerte ouvre le parcours métier correspondant, à partir des identifiants exacts et non du libellé de l'arbre.
- **Information manquante :** ouvre la fiche individuelle, avec focus ciblé si un champ d'identité connu correspond à l'alerte.
- **Pièce manquante ou bientôt périmée :** ouvre la saisie de pièce au bon type pour la bonne personne ; les dates, validations et pièces numérisées restent traitées par le dialogue existant, sans mutation automatique.
- **Contrat non signé :** ouvre la fiche sur le contrat exact ; une confirmation explicite est exigée avant d'enregistrer le statut signé.
- **DUE à faire :** ouvre le dialogue de préparation de la DPAE pour le contrat exact ; l'édition d'un PDF ne vaut pas dépôt, le statut « effectué » n'est jamais coché automatiquement.
- **Lisibilité :** les textes coupés dans la colonne gauche sont visibles entièrement en infobulle. Les catégories restent repliables/dépliables.
- **Performance et sécurité :** aucun SQL par personne ajouté : les identifiants sont associés à l'arbre dans les requêtes existantes. Le moteur conserve l'API historique de calcul lorsqu'aucune action n'est demandée.
- **Preuves automatisées :** contrôles et simulations avec données fictives, CI Linux et Windows vertes sur `5834cc31` avant passage en version. **Les interactions exactes de souris et les dialogues imbriqués restent à vérifier manuellement sous Windows.**
- **Publication :** RC6 conservée intacte, base d'exploitation non modifiée par le packaging.


## Candidate RC6 — 27 octobre 2026 (qualification utilisateur requise)

- **Création et modification des contrats sur un seul écran :** suppression du passage obligé par l'introduction, les informations complémentaires et la conclusion ; page de choix du modèle et caractéristiques immédiatement visible.
- **Validation directe :** « Valider » avec icône carrée remplace Retour/Suivant ; garde la validation du modèle, les contrôles réglementaires CCNS/CEE, le prévol final et l'enregistrement transactionnel. Le double déclenchement est protégé.
- **Compatibilité historique :** accès facultatif aux anciens champs spécifiques dans une fenêtre dédiée ; valeurs et modèles préexistants préservés, aucune donnée effacée par le changement de parcours.
- **Ergonomie :** touche Entrée pour valider le mot de passe de protection d'un fichier ; mots-clés contractuels facultatifs vides masqués dans le publiposteur avec option « Afficher aussi les champs vides ».
- **Affichage Windows :** protection candidate des onglets contre des rafraîchissements parasites ; la disparition intermittente des titres d'onglets et le scintillement doivent encore être vérifiés en vidéo sur Windows réel.
- **Recettes automatisées :** Linux, parcours critiques Windows, création de contrat CCNS, opérations CEE/CDD, popup des champs spécifiques et icône Valider verts sur le commit `24194a90` avant changement de version.
- **Réserves :** l'ancienne RC5 et la base d'exploitation ne sont pas modifiées ; le modèle Word/Writer privé doit toujours recevoir la rédaction CEE validée, et le résultat de publipostage doit être inspecté avant diffusion.


## Candidate RC5 — 27 octobre 2026 (recette visuelle Windows à confirmer)

- Assistant de publipostage : remplacer les PNG 72×24 comportant déjà du texte par de véritables icônes carrées dans Retour, Suivant, Valider, Arrêter et Fermer ; éviter toute compression des anciens sprites dans le bouton commun.
- Tableau des contrats : désactiver sous Windows les règles de liste responsables d'effacements au survol (comportement wxWidgets connu), grouper le remplissage avec Freeze/Thaw et éviter les écritures identiques de largeur de colonne.
- Contrat CEE : restauration de {CLASSIFICATION} pour les modèles anciens, clarification des trois libellés d'animateur.rice occasionnel.le selon la qualification enregistrée, et sécurisation du remplacement des champs Word/Writer.
- Corriger uniquement le code distribué : aucun contrat existant, aucune base d'exploitation ni aucun modèle Word privé n'est modifié.
- Tests automatisés Linux et Windows réussis sur le correctif préliminaire `dcd75a09`. Restent à vérifier dans le portable RC5 : rendu des boutons à 100 %/125 %, survol du tableau, et fusion Word du modèle CEE sur copie de base.


## Candidate RC4 — 14 octobre 2026 (qualification en cours)

- Préremplissage des caractéristiques du contrat dès la sélection du modèle, sans écrasement des retouches au clic sur « Suivant ».
- Réalignement des smokes Windows sur l'étape fusionnée du contrat, le contexte des modèles, l'onglet « Protection sociale » et la densité ADR-005.
- Référence des correctifs : `caa11956` sur `wx/master` (CI Linux et Windows verte avant changement de version).
- Construction du ZIP portable et de l'installateur Windows demandée par le déclencheur `[windows]` ; aucune installation ou migration de données automatisée.
- Restent à qualifier sur Windows réel : choix du modèle, recette sur copie de base, et smoke PMSL 21 h hors CI (bloqué par une modale).

## Performance

- réduction des connexions MySQL répétées au premier affichage **Individus** ;
- calcul batché de l'arbre **État des dossiers** avec une connexion bornée par rafraîchissement ;
- optimisation des écrans Individus, fiches et Présences déjà intégrée au socle 0.9.2 ;
- instrumentation de performance opt-in conservée pour la recette Windows/MySQL réelle.

## Interface

- persistance de l'ordre, de la visibilité, du tri et des largeurs des colonnes Individus ;
- suppression du redimensionnement automatique qui réimposait notamment une largeur excessive à **Téléphones** ;
- affichage Individus préparé sous gel wx puis publié en une fois ;
- corrections de géométrie wx et de zones de travail déjà intégrées au socle ;
- identité affichée alignée sur la version Teamworks-CCNS distribuée.

## Stabilité

- prise en charge des suffixes de version Teamworks-CCNS (`0.9.2-rc3`, `0.9.1f`) sans casser l'ouverture des fichiers ;
- séparation de la version du logiciel et de la version du schéma de données afin d'empêcher une RC `0.9.x` de relancer des migrations historiques 1.x/2.x ;
- réparation idempotente des tables et champs de schéma attendus à l'ouverture, notamment `sauvegardes_auto` et les champs modernes de `adresses_mail` ;
- échec explicite des parcours Windows lorsqu'une erreur SQL jusque-là silencieuse est détectée ;
- corrections des questionnaires et de leur ordre d'initialisation ;
- correction de `AttributeError: flush` à la fermeture journalisée ;
- durcissement du parcours DPAE/DUE et de ses transactions ;
- corrections des valeurs `NULL` dans les champs de publipostage ;
- protections du cycle de vie du publipostage Word/Writer ;
- corrections de plusieurs crashs et incompatibilités wxPython Phoenix présents dans la branche 0.9.2.

## Documents

- publipostage Individus indépendant de la première colonne visible ;
- corrections des mappings de mots-clés de contrats, notamment `CLASSIFICATION`, `CPNAISS` et `ADRESSERESID` ;
- fiabilisation de la fermeture et de la relance des traitements de documents.

## Nettoyage du produit

- suppression du parcours utilisateur des sollicitations commerciales historiques ;
- retrait des liens visibles vers l'ancien forum et les anciens services promotionnels ;
- remplacement de l'aide payante historique par une information Teamworks-CCNS neutre ;
- archivage séparé de l'historique upstream ancien.

## Héritage

Teamworks-CCNS dérive du projet historique Teamworks/Noethys. L'historique upstream est conservé séparément dans `docs/legacy/`.

> Cette liste décrit uniquement les changements présents dans la branche candidate 0.9.2. Les performances finales et les parcours Word/LibreOffice restent à confirmer sur le poste Windows/MySQL réel avant gel de la Vanilla.
