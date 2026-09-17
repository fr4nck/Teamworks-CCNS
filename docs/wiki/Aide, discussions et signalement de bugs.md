# Aide, discussions et signalement de bugs

<a id="aide-canaux"></a>
## Choisir le bon canal

### 1. Forum historique Teamworks

Le site historique Teamworks est conservé comme ressource d’archive : <https://www.teamworks.ovh>.

Le cœur historique du logiciel contient encore cette adresse, mais la Vanilla wx Teamworks-CCNS actuelle retire l’ancienne entrée de forum de son menu. **Ce forum n’est donc pas présenté comme le support principal du fork.**

### 2. Discussions & entraide Teamworks-CCNS

Pour une question d’utilisation, une idée ou un échange communautaire, utilisez **GitHub Discussions** du fork : <https://github.com/fr4nck/Teamworks-CCNS/discussions>.

Les échanges sont organisés par grandes thématiques afin d’éviter de mélanger installation, contrats, publipostage, données, Qt ou questionnaires dans un même fil. Voir [[Sujets et discussions]] pour les sujets conseillés et les pages du wiki à citer dans chaque échange.

### 3. Issues GitHub

Pour un bug reproductible ou une demande technique suivie, le canal attendu est **GitHub Issues** : <https://github.com/fr4nck/Teamworks-CCNS/issues>.

Au moment de cette passe documentaire, les métadonnées GitHub du dépôt indiquent que Discussions est activé mais que l’espace Issues du fork est désactivé. Si le bouton **New issue** n’est pas disponible, utilisez Discussions jusqu’à réactivation des Issues ; ne publiez pas de données sensibles pour contourner cette limitation.

<a id="preparer-signalement"></a>
## Avant de signaler un problème

Notez :

- version affichée par Teamworks ;
- RC/release et, si disponible, commit ou BUILD ;
- Windows/portable ou autre environnement ;
- dossier local ou réseau/MySQL ;
- écran et action exacte ;
- résultat attendu et résultat obtenu ;
- message d’erreur ;
- reproductibilité ;
- rapport de crash si un fichier a été créé.

Pour un problème de document, ajoutez le contexte (**Individu**, **Candidat**, **Candidature**, **Contrat**), l’éditeur et la balise concernée.

## Reproduire proprement

1. Repartir d’un état connu sans écraser des données utiles.
2. Noter les clics exacts.
3. Reproduire une seconde fois si c’est sans risque.
4. Joindre une capture seulement si elle ne montre pas de données personnelles inutiles.
5. Pour un crash, suivre [[Diagnostic et rapports de crash]].

## Aide intégrée

Plusieurs dialogues appellent encore le système d’aide historique. Lorsque cette aide et le comportement de la version installée divergent, le comportement réel de la version et ce wiki vérifié contre le code priment ; signalez l’écart documentaire.

## Informations à ne pas publier

- mots de passe ;
- chaîne MySQL complète ;
- numéro de sécurité sociale réel ;
- données personnelles sans rapport avec le bug ;
- sauvegarde de production complète dans un espace public.

## Liens associés

[[Sujets et discussions]] · [[Problèmes fréquents]] · [[Diagnostic et rapports de crash]] · [[Versions et mises à jour wx]] · [[Sauvegardes et restauration]]
