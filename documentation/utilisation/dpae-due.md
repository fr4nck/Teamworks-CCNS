# DPAE et DUE

## À quoi ça sert ?

Teamworks-CCNS wx contient un module historique d'édition **DUE/DPAE** qui prépare les informations du formulaire et produit un PDF.

!!! danger "Avertissement — pas de télétransmission"
    **Ce module génère/édite les informations du formulaire. Il ne prouve aucune télétransmission automatisée.** Le code construit un PDF par superposition de texte sur une image de formulaire (via ReportLab), puis l'ouvre localement. Aucun appel réseau vers l'Urssaf ou un autre service n'a été trouvé dans ce module ni dans les fichiers connexes.

## Où la trouver ?

Parcours confirmé : **Individus > fiche > Contrats > sélectionner un contrat > Imprimer > D.U.E.**. L'action ouvre le dialogue d'édition DUE pour le contrat sélectionné.

Le bouton/état **DUE** de la liste des contrats sert à mémoriser l'état du contrat ; cocher cet état ne déclenche pas à lui seul l'édition ni une déclaration en ligne.

## Données préremplies

Le dialogue importe des données du dossier et du contrat pour les trois catégories du formulaire :

- **Établissement employeur** : SIRET, APE, dénomination, adresses, téléphone/fax et autres paramètres employeur disponibles ;
- **Futur salarié** : identité, naissance, sécurité sociale, nationalité, adresse, date/heure d'embauche ;
- **Autres éléments** : emploi/qualification, période d'essai, durées de travail et informations contractuelles prévues par le formulaire historique.

La grille est éditable : chaque valeur modifiée est sauvegardée localement (table dédiée aux valeurs DUE), sans aucun envoi réseau.

## Données à vérifier

Avant génération, relisez particulièrement :

- SIRET et code APE ;
- identité et nom de naissance ;
- numéro de sécurité sociale ;
- date/lieu/nationalité de naissance ;
- adresse ;
- date et heure d'embauche ;
- nature du contrat, qualification et durée du travail.

Les champs du formulaire portent des identifiants comme `NUM_SIRET`, `CODE_APE` ou `CIVILITE_SALARIE`. **Ce ne sont pas des balises `{MOTCLE}` de publipostage.**

## Rendu PDF

Le module utilise ReportLab et place les valeurs aux coordonnées du formulaire PDF (superposition sur une image de fond). Le résultat attendu est un document imprimable/archivable à contrôler visuellement avant usage administratif.

## Points d'attention

- La terminologie **DUE** est historique ; cette page emploie DPAE/DUE pour retrouver le module réel.
- L'édition PDF n'est pas une preuve de dépôt ou d'accusé de réception administratif.
- Le moteur générique de publipostage ne possède pas de contexte `dpae`.
- Le résultat final du PDF et son adéquation au formulaire administratif du moment restent **à confirmer en recette fonctionnelle** avant usage réel.

## Problèmes fréquents

Si une valeur est absente, corrigez d'abord la fiche personne, le contrat ou les paramètres employeur. Si le PDF ne s'ouvre pas ou si un champ est décalé, voir [Problèmes fréquents](../reference/problemes-frequents.md).

## Voir aussi

[Contrats, CCNS et CEE](contrats-ccns-cee.md) · [Paramétrage](../administration/parametrage.md) · [Problèmes fréquents](../reference/problemes-frequents.md)
