# Aide et signalement de bugs

## Choisir le bon canal

### 1. Forum historique Teamworks

Le site historique Teamworks est conservé comme ressource d'archive : <https://www.teamworks.ovh>.

Le cœur historique du logiciel contient encore cette adresse, mais la Vanilla wx Teamworks-CCNS actuelle retire l'ancienne entrée de forum de son menu. **Ce forum n'est donc pas présenté comme le support principal du fork.**

### 2. Discussions & entraide Teamworks-CCNS

Pour une question d'utilisation, une idée ou un échange communautaire, utilisez **GitHub Discussions** du fork : <https://github.com/fr4nck/Teamworks-CCNS/discussions>.

### 3. Issues GitHub

Pour un bug reproductible ou une demande technique suivie, le canal attendu est **GitHub Issues** : <https://github.com/fr4nck/Teamworks-CCNS/issues>.

Si l'espace Issues du dépôt n'est pas activé au moment où vous lisez ceci, utilisez Discussions en attendant ; ne publiez pas de données sensibles pour contourner cette limitation.

## Avant de signaler un problème

Notez :

- version affichée par Teamworks (contenu de `VERSION`) ;
- RC/release et, si disponible, commit ;
- Windows/portable ou autre environnement ;
- dossier local ou réseau/MySQL ;
- écran et action exacte ;
- résultat attendu et résultat obtenu ;
- message d'erreur ;
- reproductibilité ;
- rapport de crash si un fichier a été créé.

Pour un problème de document, ajoutez le contexte (**Individu**, **Candidat**, **Candidature**, **Contrat**), l'éditeur utilisé et la balise concernée.

## Reproduire proprement

1. Repartir d'un état connu sans écraser des données utiles.
2. Noter les clics exacts.
3. Reproduire une seconde fois si c'est sans risque.
4. Joindre une capture seulement si elle ne montre pas de données personnelles inutiles.
5. Pour un crash, suivre [Diagnostic et rapports de crash](../administration/diagnostic.md).

## Aide intégrée

Plusieurs dialogues appellent encore le système d'aide historique. Lorsque cette aide et le comportement de la version installée divergent, le comportement réel de la version — et cette documentation, vérifiée contre le code — priment ; signalez l'écart documentaire.

## Informations à ne pas publier

- mots de passe ;
- chaîne de connexion MySQL complète ;
- numéro de sécurité sociale réel ;
- données personnelles sans rapport avec le bug ;
- sauvegarde de production complète dans un espace public.

## Voir aussi

[Problèmes fréquents](problemes-frequents.md) · [Diagnostic et rapports de crash](../administration/diagnostic.md) · [Mises à jour](../demarrage/mise-a-jour.md) · [Données, sauvegardes et MySQL](../administration/donnees-sauvegardes.md)
