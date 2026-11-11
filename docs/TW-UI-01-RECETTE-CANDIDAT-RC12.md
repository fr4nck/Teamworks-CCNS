# Teamworks-CCNS — RC12 publiée / recette TW-UI-01

**État au 11 novembre 2026 : RC12 publiée en préversion, pas qualifiée stable.**

- [Release `v0.9.2-rc12`](https://github.com/fr4nck/Teamworks-CCNS/releases/tag/v0.9.2-rc12), tag sur `9b02fbe94016b403255eabdaa856176d7f3e0ac5`.
- [Run qualifiant `42675793471`](https://github.com/fr4nck/Teamworks-CCNS/actions/runs/42675793471) : Linux 2 902 PASS / 12 SKIP, contrôles Windows et packaging réussis ; ZIP portable, installateur Windows et `SHA256SUMS.txt` présents sur la release.
- **Essai utilisateur confirmé :** ouverture de l'exécutable portable sur le 5700X / Windows 11 et récupération des paramètres de connexion de l'espace de travail. **Aucune conclusion** sur la sûreté des écritures métier ni sur la base réelle n'en découle.
- **Recette encore ouverte :** tests graphiques complets, flux métier, sauvegarde/restauration, Mailer local fictif et incidents réseau. Ne pas envoyer de messages réels pendant cette recette sans dispositif de test explicitement contrôlé.
- **Décision associée :** gel fonctionnel réversible de `wx/master` avant `v0.9.2` stable ; voir [ROADMAP](../ROADMAP.md).

Les sections techniques 1 et 2 ci-dessous conservent la **chronologie de préparation avant publication**, notamment les anciens runs échoués ; elles ne remplacent pas l'état courant ci-dessus.


## 1. Provenance du paquet — historique avant publication

- Rail : `wx/master`. Version du code candidat : `0.9.2-rc12`.
- Le workflow existant `.github/workflows/ci.yml` compile le portable via
  le marqueur de commit `[windows]`.
- Le marqueur additionnel `[candidate-only]` inhibe **expressément**
  l'étape « Publier la release GitHub ».
- La construction ne part que si les jobs tests Linux et Windows sont verts.
- L'archive `Teamworks-CCNS-0.9.2-rc12-windows-x64.zip` est remise en
  **artefact du run Actions**, non en release publique.
- Le workflow génère aussi un installeur, mais ce n'est **pas** le support
  à utiliser pour la recette isolée, afin de ne pas écrire dans le profil
  et les chemins d'installation habituels.
- La rétention des artefacts du workflow est actuellement de **3 jours**.
  Un artefact expiré devra être reconstruit ; ne pas substituer un ancien.

### Contrôle de cohérence de la version

Le run `42673834593` a constaté un défaut documentaire : `VERSION`
indiquait `0.9.2-rc12`, tandis que `README.md` et la première
entrée de `teamworks/Versions.txt` indiquaient encore RC11. Le garde
de cohérence a bloqué le packaging. Les deux références sont alignées
sur RC12 ; un nouveau run doit les vérifier avant la construction.

### Tentative de construction initiale (non qualifiante)

Le run GitHub Actions `42672838525` a obtenu **Windows PASS**,
mais GitHub Actions l'a clôturé sans avoir lancé le job Linux ni le
packaging. Aucun ZIP de recette n'en est sorti. Une nouvelle tentative
avec le même code et les mêmes garde-fous est effectuée séparément ;
seul un run complet `SUCCESS` avec archive vérifiée permettra la recette.

### Recette Windows étendue : adaptation du test après changement d'API

Le run `42674247406` a réussi les tests Linux et Windows, mais
`smoke_mailing_preparation.py` a expiré au premier envoi fictif (180 s).
Le faux transport du test implémentait l'ancienne API `Envoyer_lot()`,
alors que le Mailer utilise désormais `Connecter()/Envoyer()/Fermer()`.
Une boîte d'erreur non pilotée par le smoke restait donc modale.

Le smoke est corrigé **sans réduire ses vérifications** : il simule
`Envoyer()` message par message, refuse l'ancien `Envoyer_lot()`,
vérifie les deux envois, la fusion, la non-mutation des pièces personnelles
et la fermeture du transport. Aucun email réel n'est émis.
Cette explication a ensuite été validée par le run complet `42675793471` : les trois jobs pertinents sont réussis.

## 2. Contrôles avant essai

1. Ouvrir le run GitHub Actions du commit candidat et relever son SHA.
2. Confirmer `SUCCESS` pour les jobs **Tests et règles du socle**,
   **Parcours critiques Windows** et **Paquets Windows portable et installable**.
3. Télécharger l'artefact `Teamworks-CCNS-Windows` dans la section
   « Artifacts » de **ce même run**. Ne pas utiliser une release RC11.
4. Vérifier les SHA-256 de l'archive et de l'installeur contre
   `SHA256SUMS.txt` ; ne pas lancer l'installeur pour cette recette.
5. Décompresser uniquement l'archive portable dans un **nouveau dossier**
   sous `C:\_Atelier_IA\Teamworks-CCNS\Recette-RC12\`.
   Ne rien écrire à la racine de `C:\` ; ne déplacer ni supprimer des
   données ou versions existantes.
6. Vérifier que le `BUILD.txt` du dossier extrait contient le **même SHA**
   que le run GitHub ; vérifier `VERSION` = `0.9.2-rc12`.
7. Employer un **compte utilisateur Windows de test séparé** ou une VM
   et uniquement une base fictive. Le portable peut accéder aux paramètres
   du profil Windows courant : le dossier séparé ne suffit pas à isoler
   les données et les identifiants existants.
8. **Interdire l'accès réseau sortant** pendant la première recette
   graphique, notamment SMTP et Mailjet. N'activer que le serveur de
   messagerie local fictif lorsqu'il est effectivement configuré.
   Ne pas cliquer sur « Envoyer » si le transport fictif n'est pas installé.

## 3. Vérifications pratiques

| Vérification | Attendu |
| --- | --- |
| Démarrage du portable | Fenêtre principale visible, sans crash |
| Fenêtre maximisée | Reste maximisée après ouverture/fermeture du Mailer |
| Fenêtre normale | Pas de maximisation forcée |
| Minimisation volontaire | Possible, puis retour à la fenêtre normale |
| Ouverture et fermeture du Mailer | Aucun dialogue orphelin ni apparition « fantôme » |
| Navigation vers la configuration d'expéditeur | Aucun gel |
| Export Excel vers Mailer | La fenêtre reste rattachée à l'application |
| Tests d'envoi individuel/collectif | **Uniquement** avec le transport fictif |
| Fermeture pendant envoi fictif | Message explicite, aucun envoi doublé |
| Compte-rendu des refus/états incertains | Aucun faux succès ni renvoi automatique |
| Sauvegarde/rapport de crash | Avec dossier et base fictifs seulement |

Pour chaque essai, relever l'état (PASS/FAIL/NON TESTÉ), une capture
anonymisée si utile, le scénario et le SHA de `BUILD.txt`.

## 4. Critères de décision — passage à `v0.9.2` stable

RC12 est **déjà publiée** avec accord utilisateur ; les critères de stabilité sont une **décision distincte**. La stabilité n'est pas acquise tant que :

- les parcours critiques RH et leurs écritures n'ont pas été exercés sur **copie de données** avec fermeture/réouverture et persistance ;
- une sauvegarde et une restauration complète n'ont pas été validées sur la copie ;
- le parcours Word/Writer, les principaux dialogues, la navigation et les DPI Windows cibles ne sont pas qualifiés ;
- le Mailer complet, les fenêtres modales et les transports contrôlés n'ont pas été vérifiés, sans vrai envoi non autorisé ;
- les anomalies bloquantes/majeures identifiées ne sont pas corrigées puis requalifiées, avec résultat tracé et décision explicite de stabilisation.

**Interdit :** assimiler une CI verte, le seul lancement sur le profil existant ou une release publique à une recette métier réussie. Ne jamais modifier le tag RC12.


## 5. Registre de preuves actuel — 11 novembre 2026

| Contrôle | Statut | Preuve / limite |
| --- | --- | --- |
| Provenance code/packaging et manifestes | PASS | SHA `9b02fbe9`, run `42675793471`, `SHA256SUMS.txt` |
| Tests Linux / Windows / fabrication paquet | PASS | 2 902 PASS, 12 SKIP ; Windows et packaging SUCCESS |
| Publication GitHub avec 3 livrables | PASS | Release `v0.9.2-rc12`, préversion publique |
| Lancement du portable Windows 11 | PASS | Ouverture confirmée par l'utilisateur sur 5700X |
| Récupération des paramètres de connexion | PASS limité | Profil existant ; aucune validation SQL métier |
| Recette RH en écriture sur copie indépendante | NON TESTÉ | Ne pas écrire dans la base de production à titre d'essai |
| Sauvegarde et restauration réelle sur copie | NON TESTÉ | Tests automatisés ne remplacent pas la restauration de recette |
| Mailer graphique complet, focus, minimisation | NON TESTÉ | Banc wx fictif qualifié seulement |
| SMTP/Mailjet avec coupures réseau instrumentées | NON TESTÉ | Aucune livraison réelle démontrée |
| Publipostage Word et DPI réels 125/150 % | NON TESTÉ | Restent à valider |
| GO utilisateur pour version stable | NON DONNÉ | GO obtenu pour publication de la préversion et gel réversible wx uniquement |

Consigner les nouveaux résultats avec date, scénario, environnement, anonymisation des preuves et SHA exact du paquet. Les actions de développement et les dérogations relèvent de la roadmap unique.

