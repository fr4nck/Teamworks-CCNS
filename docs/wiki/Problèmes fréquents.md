# Problèmes fréquents

Cette page propose des vérifications simples sans inventer de correctif. Si une action risque les données, faites d’abord une sauvegarde.

<a id="probleme-demarrage"></a>
## L’application ne démarre pas

**Symptôme →** aucune fenêtre, fermeture immédiate ou rapport de crash au lancement.  
**Vérification →** chercher un fichier récent dans le dossier `Logs`, noter la version et vérifier que le paquet correspond bien à Vanilla wx.  
**Action possible →** conserver le rapport, relancer une fois depuis le même paquet ; ne supprimer ni base ni configuration au hasard.  
**Ouvrir une Issue →** si le problème est reproductible avec le rapport technique et la version. Voir [[Diagnostic et rapports de crash]].

<a id="probleme-fiche-lente"></a>
## Une fiche est très lente à ouvrir

**Symptôme →** attente visible à l’ouverture/changement d’onglet.  
**Vérification →** noter l’onglet précis, local ou MySQL, heure du test et comportement sur une connexion plus proche si possible.  
**Action possible →** distinguer latence réseau et action applicative avant de modifier les données.  
**Ouvrir une Issue →** si le même parcours reste lent de façon reproductible avec des informations de contexte mesurables. Voir [Performance MySQL](Données,-sauvegardes-et-MySQL#performance-mysql).

<a id="probleme-colonnes"></a>
## Les colonnes sont mal dimensionnées

**Symptôme →** colonnes trop étroites, mauvais ordre ou informations masquées.  
**Vérification →** ouvrir **Individus > Options**.  
**Action possible →** régler visibilité/ordre/largeur ou utiliser **Réinitialiser**.  
**Ouvrir une Issue →** si l’état ne se mémorise pas ou redevient incorrect après redémarrage. Voir [Personnaliser la liste](Individus-et-fiches#personnaliser-liste).

<a id="probleme-mysql"></a>
## Erreur MySQL

**Symptôme →** dossier réseau inaccessible, erreur de connexion ou sauvegarde réseau impossible.  
**Vérification →** hôte, port, interface MySQL, disponibilité du serveur ; ne jamais publier le mot de passe. Pour une sauvegarde, vérifier aussi la présence des outils MySQL.  
**Action possible →** tester les paramètres avec les outils prévus par Teamworks et conserver le message exact.  
**Ouvrir une Issue →** si le problème est reproductible avec version, action, hôte/port non sensibles et rapport éventuel.

<a id="probleme-publipostage"></a>
## Word ou Writer ne s’ouvre pas

**Symptôme →** le modèle ne s’ouvre pas ou la fusion externe échoue.  
**Vérification →** extension du modèle, installation de Word/COM ou de Writer/UNO/`soffice`.  
**Action possible →** vérifier d’abord avec un modèle simple et, si approprié, essayer Teamword pour isoler le problème de suite bureautique.  
**Ouvrir une Issue →** avec éditeur, version bureautique, modèle minimal non sensible et étape exacte. Voir [[Publipostage et documents]].

<a id="probleme-mot-cle-vide"></a>
## Un mot-clé est vide ou reste visible

**Symptôme →** `{MOTCLE}` vide ou non remplacé.  
**Vérification →** étape **Vérification des données du document**, contexte, orthographe/accolades/casse.  
**Action possible →** corriger la donnée source ou utiliser une balise réellement exposée.  
**Ouvrir une Issue →** si la grille contient la bonne valeur mais la fusion produit un résultat différent. Voir [[Mots-clés de publipostage]].

<a id="probleme-crash"></a>
## Teamworks affiche un rapport de crash

**Symptôme →** dialogue « Rapport de crash Teamworks CCNS ».  
**Vérification →** ouvrir le dossier Logs et identifier le rapport correspondant à l’heure du problème.  
**Action possible →** conserver le `.txt`, relire son contenu, noter les clics précédents.  
**Ouvrir une Issue →** joindre le rapport et la reproduction sans données métier supplémentaires. Voir [[Diagnostic et rapports de crash]].

<a id="probleme-licence"></a>
## Fichier de licence / enregistrement absent

**Symptôme →** écran ou message historique relatif à l’enregistrement.  
**Vérification →** confirmer que le paquet est bien celui du fork Teamworks-CCNS et noter le texte exact.  
**Action possible →** ne recopiez pas d’anciennes procédures commerciales trouvées dans un vieux manuel. Le fork retire plusieurs sollicitations historiques de l’interface actuelle.  
**Ouvrir une Issue →** si un blocage réel empêche l’usage de la Vanilla wx actuelle.

<a id="probleme-mise-a-jour"></a>
## Mise à jour indisponible

**Symptôme →** la commande de recherche de mise à jour ne propose rien ou échoue.  
**Vérification →** comparer `VERSION`/version affichée aux **Releases GitHub**.  
**Action possible →** ne pas supposer que l’updater est la source de vérité ; suivre [[Versions et mises à jour wx]].  
**Ouvrir une Issue →** si la commande wx est censée être utilisée dans votre paquet et échoue de façon reproductible. Le mécanisme reste **À confirmer en recette fonctionnelle**.

<a id="probleme-documents"></a>
## Un document ne s’ouvre pas

**Symptôme →** fichier `.twd`, `.doc`, `.odt` ou PDF non ouvert.  
**Vérification →** type de fichier, éditeur choisi, existence du fichier et droits d’accès au dossier.  
**Action possible →** ouvrir un modèle simple avec le moteur correspondant ; ne renommez pas seulement l’extension pour convertir le format.  
**Ouvrir une Issue →** avec format, point d’entrée, éditeur et message exact.

## Liens associés

[[Diagnostic et rapports de crash]] · [[Aide, discussions et signalement de bugs]] · [[Sauvegardes et restauration]]
