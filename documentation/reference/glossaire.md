# Glossaire

Vocabulaire réellement employé par Teamworks-CCNS (interface, code, contexte de publipostage). Les termes sont classés par ordre alphabétique ; chaque entrée a une ancre stable pour être liée depuis les autres pages.

### CCNS {#ccns}
Convention collective nationale du sport. Le moteur calcule certains minima et contrôles de rémunération à partir des données disponibles. Voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md) et les mots-clés [`{GROUPECCNS}`](../publipostage/mots-cles.md#publipostage-groupeccns), [`{MINIMUMCCNS}`](../publipostage/mots-cles.md#publipostage-minimumccns).

### CEE {#cee}
Contrat d'engagement éducatif. Teamworks-CCNS possède des champs/barèmes spécifiques, à distinguer d'un contrôle juridique complet. Voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md).

### Candidat {#candidat}
Personne suivie dans le module [Recrutement](../utilisation/recrutement.md) avant conversion éventuelle en Individu/Personne.

### Candidature {#candidature}
Dossier de recrutement lié à un candidat ou, après conversion, à une personne.

### Champ personnalisé {#champ-personnalise}
Donnée dont le nom est défini dans le dossier (pas dans le code) et qui peut rejoindre le publipostage selon sa configuration. Voir [Champs personnalisés](../publipostage/mots-cles.md#champs-personnalises).

### Contrat {#contrat}
Engagement rattaché à une personne, avec type, dates, durée, rémunération et données CCNS/CEE selon le cas. Voir [Contrats, CCNS et CEE](../utilisation/contrats-ccns-cee.md).

### DPAE / DUE {#dpae-due}
Module d'édition du formulaire de déclaration préalable à l'embauche. L'édition PDF ne prouve pas une télétransmission officielle. Voir [DPAE et DUE](../utilisation/dpae-due.md).

### Dossier local {#dossier-local}
Dossier Teamworks-CCNS stocké dans les fichiers de données locaux, notamment `<nom>_TDATA.dat`.

### Dossier réseau {#dossier-reseau}
Dossier Teamworks-CCNS utilisant le mode `[RESEAU]`, généralement adossé à MySQL.

### Individu {#individu}
Terme d'interface pour une personne suivie dans le dossier principal. Voir [Personne](#personne) pour le terme équivalent côté données.

### MySQL {#mysql}
Moteur de base utilisé par le mode réseau ; distinct du stockage local SQLite. Voir [Données, sauvegardes et MySQL](../administration/donnees-sauvegardes.md).

### Mot-clé {#mot-cle}
Balise de modèle sous la forme `{MOTCLE}`, remplacée par une valeur du contexte au moment du publipostage. Voir la [référence des mots-clés](../publipostage/mots-cles.md).

### Personne {#personne}
Objet de données correspondant à l'Individu ; ce nom apparaît notamment dans le code et le contexte de publipostage.

### Publipostage {#publipostage}
Fusion d'un modèle avec les données d'un ou plusieurs éléments/personnes. Voir [Documents et publipostage](../utilisation/documents.md).

### Qt {#qt}
Trajectoire d'interface à l'étude, sans code livré à ce jour. Ses fonctions ne doivent jamais être déduites du comportement wx. Voir [Trajectoire Qt](../architecture/qt.md).

### RC (release candidate) {#rc}
Version candidate à la publication, qui nécessite encore une qualification avant d'être considérée stable. Voir [Mises à jour](../demarrage/mise-a-jour.md).

### Teamword {#teamword}
Éditeur de texte enrichi intégré à Teamworks-CCNS (composant `wx.richtext.RichTextCtrl`), utilisé pour les modèles `.twd` et la composition d'email HTML. Voir [Éditeur interne](../utilisation/editeur.md).

### Vanilla wx {#vanilla-wx}
Application Teamworks-CCNS basée sur wxPython — seul rail d'interface disponible aujourd'hui.

## Terminologie recommandée

Cette documentation emploie de façon cohérente : **Teamworks-CCNS**, **Vanilla wx**, **Teamword**, **Microsoft Word**, **LibreOffice Writer**, **Discussions GitHub**, **Issues GitHub**.

## Voir aussi

[Accueil](../index.md) · [Architecture — vue d'ensemble](../architecture/vue-ensemble.md) · [Historique du projet](../historique/origine-et-wiki.md)
