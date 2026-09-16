# Individus et fiches

L’espace **Individus** est la liste de travail principale des personnes enregistrées dans le dossier.

## La liste des individus

La page affiche une liste, une zone **État des dossiers**, un résumé de la sélection et une barre **Rechercher un individu**. Les actions présentes sont : ajouter, modifier, supprimer, rechercher par période de présence, afficher tout, options de liste, courrier/publipostage, imprimer, exporter en texte, exporter en Excel et aide.

### Rechercher et trier

- Tapez dans **Rechercher un individu** : le filtre porte sur les colonnes de la liste.
- Cliquez sur une colonne pour trier.
- Redimensionnez une colonne en faisant glisser sa séparation : les largeurs et le tri sont mémorisés dans la configuration wx.
- Les options de liste permettent de revenir aux choix de présentation ; l’ajustement automatique ne réécrase plus les largeurs choisies par l’utilisateur.

### Exporter

**Exporter texte** produit un export texte de la liste. **Exporter Excel** est disponible sur les plateformes où cette action est activée ; le bouton est explicitement désactivé sous Linux dans l’interface wx actuelle.

## Créer une fiche

1. Cliquez sur **Ajouter**.
2. La fiche s’ouvre sur **Généralités** et crée l’enregistrement de base.
3. Enregistrez les généralités ; les autres onglets deviennent alors disponibles.
4. Complétez progressivement le dossier plutôt que d’inventer des valeurs manquantes.

## Onglets de la fiche individuelle

La fiche wx actuelle contient exactement les onglets suivants :

- **Généralités** — identité et informations principales ;
- **Questionnaire** — champs de questionnaire configurés ;
- **Qualifications** — qualifications/diplômes ;
- **Contrats** — contrats rattachés ;
- **Présences** — présences de la personne ;
- **Scénarios** — scénarios rattachés ;
- **Frais** — frais de la personne ;
- **Recrutement** — candidatures rattachées.

Le changement d’onglet sauvegarde les généralités quittées ; après cette première sauvegarde, l’annulation de toute la création n’est plus équivalente à « aucune donnée créée ».

## Modifier une fiche

Sélectionnez une personne puis cliquez sur **Modifier**, ou double-cliquez sa ligne. L’en-tête reprend le nom, l’adresse, la naissance et la photo. Une barre de problèmes peut signaler des points à contrôler sur le dossier.

## Supprimer une fiche

Le bouton **Supprimer** agit sur la personne sélectionnée. Cette opération est destructive : avant de confirmer, contrôlez les contrats, présences, frais et candidatures associés et assurez-vous de disposer d’une sauvegarde.

## Données historiques incomplètes

La liste modernisée est volontairement tolérante aux références historiques cassées. Au lieu de planter, elle peut afficher par exemple **Pays introuvable (réf. …)**, **Nationalité introuvable**, **Situation introuvable** ou **Diplôme introuvable**. Ces libellés indiquent une donnée à corriger ; ils ne constituent pas une valeur métier normale.

## Publipostage depuis Individus

Le bouton courrier de la liste lance `CourrierPublipostage(mode='multiple')` et ouvre l’assistant pour les personnes sélectionnées. L’étape de vérification montre les valeurs exactes qui seront fusionnées.

## Mots-clés de publipostage liés aux individus

Les plus utilisés sont :

- [`{CIVILITE}`](Mots-clés-de-publipostage#publipostage-civilite)
- [`{NOM}`](Mots-clés-de-publipostage#publipostage-nom)
- [`{PRENOM}`](Mots-clés-de-publipostage#publipostage-prenom)
- [`{DATENAISS}`](Mots-clés-de-publipostage#publipostage-datenaiss)
- [`{ADRESSERESID}`](Mots-clés-de-publipostage#publipostage-adresseresid)
- [`{CPRESID}`](Mots-clés-de-publipostage#publipostage-cpresid)
- [`{VILLERESID}`](Mots-clés-de-publipostage#publipostage-villeresid)
- [`{TELEPHONES}`](Mots-clés-de-publipostage#publipostage-telephones)
- [`{EMAILS}`](Mots-clés-de-publipostage#publipostage-emails)

Le contexte Individu expose 18 mots-clés standard. Voir [[Mots-clés de publipostage]] pour la liste exhaustive, les formats et les contextes hérités.

## En cas de problème

- Si une valeur n’apparaît pas dans un document, regardez d’abord la grille **Vérification des données du document** de l’assistant.
- Si la liste signale une référence introuvable, corrigez la donnée de la fiche avant de produire un document officiel.
- Si les colonnes sont devenues peu lisibles, utilisez les options/réinitialisation de présentation plutôt que de supprimer la configuration entière.
