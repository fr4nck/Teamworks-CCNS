# Audit de sortie Connecthys

Date de l’audit : 5 septembre 2026  
Branche : `audit/sortie-connecthys`  
Périmètre : dépôt `fr4nck/Teamworks-CCNS` et contrôles externes à préparer.  

> Cet audit vise à objectiver les dépendances résiduelles. Il ne résilie aucun service, ne migre pas l’interface Qt, ne décide pas du rapatriement du service de switch et ne change pas l’hébergement du Portail.

## 1. Résumé exécutif

- **Dépendance Connecthys trouvée dans le dépôt : NON pour une référence explicite active, sous réserve du garde-fou automatique sur le checkout complet.** Les recherches manuelles n’ont pas mis en évidence d’appel, endpoint ou secret explicitement nommé Connecthys. Les occurrences génériques réseau, synchronisation, messagerie, stockage de paramètres et sauvegarde restent des **candidats à qualifier**, pas des dépendances Connecthys confirmées.
- **Résiliation techniquement possible aujourd’hui : NON DÉMONTRÉ.** Le dépôt ne contient ni la configuration réelle des postes, ni les valeurs de la base en production, ni les tâches Windows, ni les règles DNS/pare-feu, ni les journaux réseau, ni le contrat Connecthys.
- **Dépendances Connecthys confirmées dans le dépôt : 0.**
- **Classes de candidats techniques à contrôler hors dépôt : 5** : configuration utilisateur ; table `parametres` ; sauvegardes automatiques ; configuration de messagerie ; paramètres de connexion base/réseau et certificats.
- **Principaux bloqueurs** : absence de preuve sur la configuration et la base réelles, absence de test de coupure contrôlée, absence d’inventaire des tâches/services Windows et du trafic, absence de vérification des liens encore distribués aux utilisateurs, récupération/effacement des données et échéance contractuelle non vérifiés.
- **Prochaines actions** : exécuter le scanner sur le checkout complet ; interroger les tables de configuration sans exposer les secrets ; inventorier poste/serveur/tâches/services ; relever les domaines Connecthys réels ; réaliser une coupure ciblée en recette ; valider les parcours métier ; vérifier export, RGPD et contrat.

### Verdict

**CONNECTHYS : NON DÉMONTRÉ**

L’absence de dépendance explicite dans le code n’est pas une preuve de résiliabilité. La sortie ne pourra être déclarée prête qu’après les contrôles externes et la coupure réelle décrits ci-dessous.

## 2. Méthode et preuves dépôt

L’audit distingue quatre états :

- **confirmée** : preuve directe d’un appel, d’un stockage, d’un endpoint ou d’un mécanisme actif ;
- **candidate** : mécanisme pouvant héberger une dépendance, sans preuve qu’il pointe vers Connecthys ;
- **historique / morte** : référence non atteignable ou documentaire ;
- **hors dépôt** : vérification impossible depuis GitHub seul.

Le garde-fou `tools/audit_connecthys.py` analyse les fichiers suivis par Git et inventorie séparément : marque Connecthys, URLs, primitives réseau, synchronisation/portail, marqueurs d’authentification, automatisation, stockage de configuration et sémantique import/export. Avec `--fail-on-active-brand`, seule une référence explicite à Connecthys dans un périmètre actif est bloquante. `tests/test_audit_connecthys.py` vérifie notamment qu’une référence de documentation ne devient pas un faux positif bloquant et que les candidats réseau restent distincts d’une dépendance confirmée.

Commande de contrôle :

```bash
python tools/audit_connecthys.py . --fail-on-active-brand --json /tmp/connecthys-audit.json --markdown /tmp/connecthys-audit.md
pytest -q tests/test_audit_connecthys.py
```

La suite CI existante exécute déjà `pytest` ; le test d’intégration du scanner audite le dépôt réel et échoue si une référence Connecthys active est détectée.

## 3. Cartographie des dépendances et candidats

| Emplacement | Type | Appelant / déclencheur | Usage observé | Criticité | Statut | Remplacement nécessaire ? |
| --- | --- | --- | --- | --- | --- | --- |
| `teamworks/Teamworks_core.py` | réseau HTTP | démarrage de Teamworks | vérification de version via GitHub/`teamworks.ovh`; liens d’aide Teamworks | faible à moyenne | **Confirmée, non Connecthys** | Non pour la sortie Connecthys ; vérifier que le domaine n’est pas fourni par le contrat Connecthys |
| `teamworks/Utils/UTILS_Config.py` | configuration utilisateur | démarrage / préférences | `Config.json` dans le profil utilisateur | moyenne | **Candidate** | À déterminer après inspection d’un poste |
| `teamworks/Utils/UTILS_Customize.py` | configuration utilisateur | interface | `Customize.ini` dans le profil utilisateur | faible | **Candidate** | À déterminer après inspection d’un poste |
| `teamworks/Utils/UTILS_Fichiers.py` | fichiers utilisateur | bootstrap / migrations locales | dossiers `Data`, `Temp`, `Sync`, `Modeles`, `Editions`; déplacement d’anciens fichiers `Sync` | moyenne | **Candidate** | Le rôle réel de `Sync` doit être qualifié |
| `teamworks/Utils/UTILS_Parametres.py` | base de données | nombreux modules | table `parametres`, valeurs arbitraires par catégorie/nom | élevée | **Candidate** | À déterminer sur copie réelle de la base |
| `teamworks/GestionDB.py` | base MySQL distante | ouverture d’un fichier `[RESEAU]` | host, port, utilisateur, mot de passe encodé et certificats SSL utilisateur | critique pour DB réseau | **Confirmée, non Connecthys à ce stade** | Ne pas supprimer : l’architecture cible conserve les bases métier sur serveur |
| `teamworks/Utils/UTILS_Sauvegarde_auto.py` | automatisation | fermeture/changement de fichier et action manuelle | règles en table `sauvegardes_auto`, fichiers réseau, répertoire cible, e-mails, horaires/postes | élevée | **Candidate** | Oui seulement si une cible Connecthys est trouvée |
| `teamworks/Utils/UTILS_Sauvegarde.py` | export/sauvegarde | sauvegarde automatique/manuelle | `mysqldump`, ZIP, copie vers répertoire configuré, envoi e-mail éventuel | élevée | **Candidate** | Oui seulement si destination ou messagerie dépend de Connecthys |
| `teamworks/Utils/UTILS_Envoi_email.py` + `UTILS_Mailing.py` | messagerie | mailer, sauvegardes, rapports | SMTP ou Mailjet ; paramètres et secrets issus de la base | moyenne à élevée | **Candidate** | Oui seulement si SMTP/API est fourni par Connecthys |
| `teamworks/Utils/UTILS_Envoi_rapport_bug.py` | messagerie | action utilisateur explicite depuis rapport de crash | envoi du rapport via expéditeur configuré ; destinataire configurable en base | faible | **Candidate** | Vérifier la configuration réelle |

### Conclusion sémantique du dépôt

Aucun mécanisme observé ci-dessus ne permet, par son nom ou son comportement seul, d’affirmer qu’il dépend de Connecthys. Les connexions MySQL, SMTP/Mailjet, sauvegardes et mises à jour sont des mécanismes génériques. Ils ne doivent ni être supprimés ni requalifiés comme Connecthys sans preuve de configuration réelle.

## 4. Éléments hors dépôt à vérifier

### 4.1 Poste Windows de recette

Rechercher la marque, les domaines et chemins Connecthys dans les emplacements utilisateur :

```powershell
$roots = @(
  $env:APPDATA,
  $env:LOCALAPPDATA,
  $env:PROGRAMDATA,
  "$env:USERPROFILE\Documents",
  "$env:USERPROFILE\Desktop"
) | Where-Object { $_ -and (Test-Path $_) }

Get-ChildItem $roots -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -lt 20MB } |
  Select-String -Pattern 'Connecthys','connecthys' -SimpleMatch -ErrorAction SilentlyContinue
```

Contrôler également les fichiers `Config.json`, `Config.json.bak`, `Customize.ini`, le dossier `Sync`, les certificats `ca-cert.pem`, `client-key.pem`, `client-cert.pem` et tout raccourci/launcher Teamworks ou Noethys. Un résultat négatif doit être conservé avec la date, le poste et les chemins réellement contrôlés.

### 4.2 Planificateur de tâches, services et démarrage

```powershell
Get-ScheduledTask | ForEach-Object {
  $t = $_
  $actions = ($t.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' ; '
  [pscustomobject]@{TaskPath=$t.TaskPath; TaskName=$t.TaskName; Actions=$actions}
} | Where-Object { $_.Actions -match 'connecthys|portail|sync|teamworks|noethys' }

Get-CimInstance Win32_Service |
  Where-Object { $_.Name -match 'connecthys|teamworks|noethys' -or $_.PathName -match 'connecthys|portail|sync|teamworks|noethys' } |
  Select-Object Name, State, StartMode, PathName

Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
```

Toute tâche/service trouvé doit être qualifié par propriétaire, commande, fréquence, données traitées et effet d’une désactivation.

### 4.3 Base réelle

Exécuter sur une copie de recette. Ne jamais exporter les mots de passe dans le compte-rendu.

```sql
SELECT IDparametre, categorie, nom, parametre
FROM parametres
WHERE LOWER(categorie) LIKE '%connect%'
   OR LOWER(nom) LIKE '%connect%'
   OR LOWER(parametre) LIKE '%connecthys%'
   OR LOWER(parametre) LIKE '%portail%'
   OR LOWER(parametre) LIKE '%sync%'
   OR LOWER(parametre) LIKE '%http%';
```

Inventorier les sauvegardes automatiques :

```sql
SELECT IDsauvegarde, nom, date_derniere,
       sauvegarde_repertoire, sauvegarde_emails,
       sauvegarde_fichiers_locaux, sauvegarde_fichiers_reseau,
       condition_heure, condition_poste, condition_derniere, condition_utilisateur
FROM sauvegardes_auto;
```

Inventorier les backends e-mail **sans sélectionner `motdepasse`** :

```sql
SELECT IDadresse, moteur, adresse, nom_adresse, smtp, port,
       defaut, connexionAuthentifiee, startTLS, utilisateur, parametres
FROM adresses_mail;
```

Si `parametres` contient des secrets API sérialisés, le relevé d’audit doit seulement noter leur présence, leur fournisseur et leur propriétaire ; ne pas copier les valeurs.

### 4.4 Serveur, DNS et pare-feu

À contrôler par l’administrateur :

- DNS internes et publics contenant `connecthys` ou les domaines fournis par Connecthys ;
- règles de pare-feu/proxy/NAT autorisant ces domaines/IP ;
- fichiers de configuration, variables d’environnement, scripts de sauvegarde et crons du serveur ;
- journaux proxy/DNS/pare-feu pendant une journée représentative ;
- éventuels montages réseau ou répertoires de sauvegarde hébergés par Connecthys.

Le service de switch n’est **pas** supposé être rapatrié sur le serveur : il doit être audité comme dépendance séparée, sans décision d’architecture implicite.

### 4.5 Noethys et usages périphériques

Le dépôt Teamworks-CCNS ne prouve pas l’état d’une installation Noethys distincte. Sur le poste de recette, contrôler : configuration, raccourcis, plugins, tâches planifiées, modèles d’e-mail/courriers, URLs de portail, exports/imports et logs Noethys. Une absence de référence dans Teamworks ne vaut pas absence dans Noethys.

### 4.6 Liens distribués aux utilisateurs

Contrôler les modèles et contenus réellement utilisés, y compris ceux stockés en base ou hors dépôt :

- modèles d’e-mail et publipostage ;
- courriers/PDF déjà distribués ;
- signatures e-mail ;
- favoris, raccourcis et pages d’accueil ;
- QR codes ;
- documentation familles/salariés/administrateurs ;
- messages automatiques.

Chercher les URL Connecthys réelles et tester leur remplacement avant résiliation.

## 5. Test de coupure contrôlée

### 5.1 Préparation

1. Travailler sur un poste de recette et une copie récente des bases, jamais sur la production.
2. Exécuter le scanner du dépôt et conserver ses rapports JSON/Markdown.
3. Relever dans la configuration réelle, les logs DNS/proxy et la base la liste **exacte** des domaines/IP Connecthys. Ne pas utiliser une liste supposée.
4. Sauvegarder la configuration du poste et noter les règles réseau avant modification.
5. Vérifier qu’un accès de secours permet de rétablir immédiatement les règles.

### 5.2 Coupure

Bloquer **uniquement** les domaines/IP Connecthys identifiés, idéalement via DNS/pare-feu de recette. Ne pas bloquer `teamworks.ovh`, GitHub, MySQL, SMTP/Mailjet ou le serveur PMSL35 sauf si une preuve établit qu’ils font partie de Connecthys.

### 5.3 Parcours métier à exécuter

- démarrer Teamworks et ouvrir la base habituelle ;
- ouvrir/fermer puis rouvrir un fichier métier ;
- consulter/créer/modifier une personne ;
- consulter/saisir des présences ;
- utiliser les écrans recrutement/contrats représentatifs ;
- produire un document/PDF représentatif ;
- préparer puis envoyer un e-mail de recette si le canal e-mail fait partie du périmètre ;
- exécuter une sauvegarde manuelle ;
- déclencher, si possible en recette, une sauvegarde automatique correspondant aux règles réelles ;
- vérifier la restauration d’une sauvegarde sur une cible isolée ;
- fermer Teamworks et vérifier les actions de fermeture ;
- relancer Teamworks ;
- exécuter les parcours Noethys réellement utilisés ;
- tester les fonctions historiques de portail encore utilisées : consultation, réservations, documents, factures/reçus, paiements, informations personnelles, messages et authentification, uniquement lorsqu’elles existent encore dans les usages PMSL35.

### 5.4 Observabilité

Pendant les parcours :

- conserver `journal.log` et les rapports `Logs` de Teamworks ;
- surveiller les erreurs UI et les délais anormaux ;
- relever DNS, connexions TCP sortantes et logs proxy/pare-feu ;
- relever l’historique du Planificateur de tâches ;
- vérifier les logs MySQL et messagerie si disponibles ;
- noter toute tentative vers un domaine Connecthys bloqué avec heure, processus et parcours déclencheur.

Chaque erreur doit être classée : **bloquante**, **dégradation acceptable**, **sans rapport avec Connecthys**, ou **à investiguer**.

### 5.5 Rétablissement

1. Retirer les règles de blocage.
2. Purger le cache DNS si nécessaire.
3. Refaire le parcours ayant échoué.
4. Confirmer que le retour du réseau Connecthys explique réellement la différence avant de qualifier la dépendance comme confirmée.

## 6. Tableau de sortie Connecthys

| Contrôle | Emplacement | Preuve attendue | Responsable | Statut |
| --- | --- | --- | --- | --- |
| Référence explicite Connecthys dans code actif | dépôt complet | scanner à 0 occurrence active | Développement | En cours |
| URLs/endpoints externes | dépôt + rapport scanner | inventaire qualifié, chaque domaine rattaché à un propriétaire | Développement | En cours |
| Configuration utilisateur | postes Windows | recherche `Config.json`, `Customize.ini`, `Sync`, raccourcis : résultat archivé | Support/IT | À faire |
| Paramètres applicatifs | table `parametres` | requête SQL + qualification des résultats | Référent Teamworks | À faire |
| Base métier | copie de recette | recherche de domaines/URLs/identifiants Connecthys dans les tables pertinentes | DBA / référent Teamworks | À faire |
| Connexion base réseau | `GestionDB.py` + configuration réelle | host/port/propriétaire connus ; preuve que la DB PMSL35 reste accessible sans Connecthys | IT/DBA | À faire |
| Sauvegardes automatiques | `sauvegardes_auto` | chaque destination, mail et fichier réseau qualifié | IT/DBA | À faire |
| Sauvegarde/export des données | Teamworks + Connecthys | export complet récupéré, lisible et conservé selon politique | Direction/IT | À faire |
| Restauration | environnement isolé | restauration réussie d’un jeu de sauvegarde récent | IT/DBA | À faire |
| Messagerie | `adresses_mail` | fournisseur SMTP/API identifié ; aucun secret Connecthys nécessaire | IT | À faire |
| Tâches planifiées | Windows/serveur | export des tâches + zéro action Connecthys nécessaire | IT | À faire |
| Services/démarrage | Windows/serveur | inventaire services + clés Run/startup | IT | À faire |
| Scripts | postes/serveur hors dépôt | recherche marque/domaines + qualification | IT | À faire |
| Trafic réseau | poste de recette + pare-feu/proxy | zéro tentative Connecthys pendant parcours représentatifs | IT | À faire |
| Logs | Teamworks/Windows/serveur | aucune erreur fonctionnelle due au blocage | IT + métier | À faire |
| Comptes/secrets | coffre/config/Connecthys | inventaire des comptes ; plan de révocation après validation | Direction/IT | À faire |
| Liens utilisateurs | mails, PDF, docs, QR, raccourcis | zéro URL Connecthys encore distribuée | Communication/métier | À faire |
| Documentation | interne/externe | références Connecthys retirées ou marquées historiques | Métier | À faire |
| Noethys | poste de recette | parcours et configuration vérifiés sous coupure | Référent Noethys | À faire |
| Test de coupure | recette | blocage ciblé + journal de résultats + rétablissement validé | IT + métier | À faire |
| Recette métier | Teamworks/Noethys | procès-verbal des parcours critiques | Utilisateurs référents | À faire |
| RGPD | registre/DPA/Connecthys | données exportées ; sort final, délai d’effacement, sous-traitants et preuve de suppression définis | DPO/Direction | À faire |
| Échéance contractuelle | contrat Connecthys | préavis, date limite, coûts, modalités de sortie confirmés | Direction | À faire |

## 7. Critère de sortie

La résiliation ne sera considérée techniquement prête que lorsque les preuves suivantes seront simultanément obtenues :

- zéro flux Connecthys nécessaire ;
- zéro tâche automatique Connecthys nécessaire ;
- zéro secret Connecthys nécessaire ;
- zéro URL Connecthys encore distribuée ;
- toutes les données nécessaires récupérées et vérifiées ;
- sauvegarde et restauration validées ;
- fonctionnement métier Teamworks et Noethys validé pendant une coupure contrôlée ;
- aucun blocage administratif, RGPD ou contractuel identifié.

Tant qu’un de ces points reste `À faire` ou `Bloquant`, le verdict reste :

**CONNECTHYS : NON DÉMONTRÉ**

## 8. Validation de cette PR

À renseigner avec les résultats exacts du commit final :

- `python tools/audit_connecthys.py . --fail-on-active-brand --json /tmp/connecthys-audit.json --markdown /tmp/connecthys-audit.md` ;
- `pytest -q tests/test_audit_connecthys.py` ;
- suite `pytest` Linux du dépôt via CI ;
- validations Windows prévues par le workflow du dépôt ;
- limites : aucune base PMSL35 réelle, aucun poste Windows PMSL35, aucun serveur, aucun trafic réseau réel et aucun contrat Connecthys n’ont été inspectés depuis GitHub.
