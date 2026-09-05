# Audit technique de sortie Connecthys

Date de l'audit : 5 septembre 2026  
Dépôt : `fr4nck/Teamworks-CCNS`  
Branche : `audit/sortie-connecthys`  
Périmètre exclu : PR Qt #366 (`poc/qt-theme-isole`), migration Qt, hébergement futur du Portail, rapatriement éventuel du service de switch.

> Principe de preuve : **détecté ≠ confirmé**. Une chaîne, une URL, un mot comme `sync` ou un commentaire ne constitue pas à lui seul une dépendance active.

## 1. Résumé exécutif

### Verdict

**CONNECTHYS : NON DÉMONTRÉ**

- Dépendance Connecthys trouvée dans le dépôt : **OUI, mais uniquement sous forme de références résiduelles/historiques à ce stade**.
- Résiliation techniquement possible aujourd'hui : **NON DÉMONTRÉ**.
- Dépendances Connecthys confirmées dans le code exécuté : **0**.
- Candidats Connecthys spécifiques dans le code actif : **1 chemin historique à qualifier**, dans l'updater.
- Occurrences explicites `Connecthys` détectées par le scanner sur le dépôt : **3** lors du premier passage CI ; une seule se trouve dans un fichier classé actif, dans un commentaire de `teamworks/Dlg/DLG_Updater.py`.
- Principaux bloqueurs : **base réelle non contrôlée, postes Windows non contrôlés, tâches/services non contrôlés, configuration Noethys non contrôlée, trafic réel non observé, liens distribués non inventoriés hors dépôt, données/export-restauration non validés, test de coupure non exécuté, contrat/RGPD non vérifiés**.

La lecture du dépôt permet donc de réduire fortement l'incertitude mais **ne permet pas d'autoriser une résiliation**. Le critère de sortie exige encore des preuves externes au dépôt et une coupure contrôlée.

### Fait important : résidu historique dans l'updater

`teamworks/Dlg/DLG_Updater.py` contient :

```python
# Met en pause le serveur Connecthys si besoin
try:
    self.parent.ctrl_serveur_portail.PauseServeur()
except:
    pass
```

L'updater est ouvert depuis `Teamworks_core.MyFrame.On_outils_updater()` avec `self` comme parent. L'inspection de `Teamworks_core.MyFrame` ne montre aucune définition de `ctrl_serveur_portail`. Dans cette version du dépôt, l'accès à cet attribut lève donc une exception immédiatement absorbée par le `except` silencieux. Ce bloc est qualifié **historique / mort**, et non comme preuve d'un serveur Connecthys encore utilisé.

Il n'est pas supprimé dans cette PR afin de ne pas introduire une modification de production non nécessaire à l'obtention de la preuve. Sa suppression pourra faire l'objet d'un nettoyage séparé, avec test ciblé, si souhaité.

### Autres services externes observés, non attribuables à Connecthys

Le dépôt contient des accès réseau qui doivent être distingués de Connecthys :

- mise à jour Teamworks via `teamworks.ovh` et `raw.githubusercontent.com` ;
- enregistrement/aide via `teamworks.ovh` ;
- calendrier scolaire via `education.gouv.fr` ;
- références réglementaires (Legifrance, OpenPaye, etc.) ;
- messagerie SMTP et Mailjet ;
- un client de boîte aux lettres inter-domaines RH dans `application/services/inter_domain_mailbox_client_hr.py`.

Ces flux ne doivent **pas** être bloqués pendant le test de coupure Connecthys tant qu'aucune preuve ne les relie à Connecthys.

### Prochaines actions prioritaires

1. Relever les domaines/IP/ports réellement associés au contrat Connecthys à partir de la facture, du contrat, des DNS et des configurations réelles.
2. Scanner la base réelle, notamment `parametres`, `adresses_mail` et `sauvegardes_auto`, sans extraire de secrets dans les rapports.
3. Inspecter les postes Windows, services, démarrages et Planificateur de tâches.
4. Inspecter Noethys séparément : configuration, modules, portail, synchronisations, tâches et données.
5. Inventorier les URL encore distribuées aux familles/salariés/administrateurs.
6. Vérifier export, sauvegarde et restauration des données nécessaires avant résiliation.
7. Exécuter la coupure contrôlée décrite en section 4 et conserver les preuves réseau/logs.
8. Vérifier l'échéance contractuelle, les obligations de restitution/suppression de données et les points RGPD.

---

## 2. Cartographie

### 2.1 Références Connecthys spécifiques

| Emplacement | Type | Appelant | Usage observé | Criticité | Statut | Remplacement nécessaire |
| --- | --- | --- | --- | --- | --- | --- |
| `teamworks/Dlg/DLG_Updater.py` — bloc `ctrl_serveur_portail.PauseServeur()` | Résidu portail/Connecthys | `Teamworks_core.MyFrame.On_outils_updater()` ouvre `DLG_Updater.Dialog(self)` | Tentative de pause d'un ancien serveur portail au démarrage de l'updater | Faible dans l'état observé : exception absorbée, attribut absent du parent inspecté | **Historique / morte** | Non pour la résiliation ; suppression de nettoyage possible ultérieurement |
| Deux autres occurrences explicites détectées hors périmètre actif lors du scan initial | Référence textuelle | Non démontré actif | Conservées comme traces de l'historique | Nulle tant qu'elles restent hors code actif | **Historique / morte à confirmer par le rapport de scan final** | Non |

### 2.2 Candidats génériques nécessitant une qualification

| Emplacement | Type | Appelant / activation | Usage | Criticité | Statut | Action |
| --- | --- | --- | --- | --- | --- | --- |
| `teamworks/Utils/UTILS_Parametres.py` + table `parametres` | Configuration en base | Toute fonctionnalité utilisant les paramètres | Les valeurs réelles peuvent contenir URL, domaine, identifiant ou option absents du code | Haute pour l'audit | **Possible / candidate hors dépôt** | Requête sur la base réelle |
| `teamworks/Utils/UTILS_Envoi_email.py` + table `adresses_mail` | Réseau / secrets | Envoi d'e-mails | SMTP ou Mailjet ; hôte et secrets stockés en configuration/base | Moyenne | **Dépendance externe confirmée, non attribuée à Connecthys** | Vérifier que l'hôte réel n'est pas un service Connecthys ; ne jamais publier les secrets |
| `teamworks/Dlg/DLG_Config_sauvegarde.py`, `teamworks/Dlg/DLG_Saisie_procedure_sauvegarde.py`, `teamworks/Utils/UTILS_Sauvegarde_auto.py`, table `sauvegardes_auto` | Sauvegarde automatique / réseau / e-mail | Conditions jours/heures/postes ; lancement possible sans confirmation | Sauvegarde locale/réseau et envoi possible ; destinations stockées hors code | Haute | **Possible / candidate hors dépôt** | Examiner toutes les procédures et destinations réelles |
| `teamworks/Utils/UTILS_Fichiers.py` et dossiers utilisateur `Sync` | Stockage local de synchronisation | Initialisation Teamworks / migration de répertoires | Dossier nommé `Sync`, sans preuve d'un transport Connecthys | Faible | **Candidate générique, non Connecthys** | Vérifier le contenu d'un poste réel ; ne pas conclure sur le nom seul |
| `teamworks/Dlg/DLG_Updater.py`, `Teamworks_core.py` | HTTP / mise à jour | Menu de mise à jour et contrôle au démarrage | Appels `teamworks.ovh` et GitHub | Moyenne | **Externe confirmé, non Connecthys démontré** | Ne pas inclure dans le blocage Connecthys sans preuve DNS/contractuelle |
| `application/services/inter_domain_mailbox_client_hr.py` | HTTP sortant / synchronisation | Service applicatif RH | Pull inter-domaines configurable | À qualifier | **Candidate générique, non Connecthys** | Contrôler sa configuration réelle et son endpoint |

### 2.3 Résultat du ratissage automatisé initial

Le premier passage de `tests/test_audit_connecthys.py` dans la CI a analysé **1 255 fichiers texte suivis** et signalé **827 fichiers non traités comme texte**. Il a remonté **3 occurrences explicites de Connecthys**, **96 occurrences d'URL**, **67 indices d'API réseau**, **103 indices sync/portail** et **299 indices d'automatisation**. Ces volumes sont volontairement larges et contiennent de nombreux faux positifs ; ils servent à orienter l'analyse humaine, pas à compter des dépendances.

Le premier passage a échoué parce que la mention historique de l'updater était dans un fichier actif. La garde a ensuite été affinée : une mention en commentaire reste inventoriée mais n'est plus assimilée à une dépendance exécutable. Une nouvelle référence Connecthys en code exécutable reste bloquante.

---

## 3. Éléments hors dépôt

Aucun point ci-dessous n'est considéré conforme sans preuve sur l'environnement réel.

### 3.1 Base de données réelle

#### Table `parametres`

Rechercher sans afficher de secrets :

```sql
SELECT categorie, nom, parametre
FROM parametres
WHERE LOWER(COALESCE(categorie, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(nom, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%portail%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%http%';
```

Preuve positive : domaine, URL, token, identifiant ou option identifiable comme Connecthys.  
Preuve négative : export horodaté de la requête avec zéro résultat Connecthys, plus revue des paramètres URL/portail restants.

#### Table `adresses_mail`

Inspecter les **métadonnées uniquement** : moteur, hôte, port, utilisateur, paramètres. Ne jamais copier les mots de passe, clés API ou secrets dans la PR.

```sql
SELECT IDadresse, moteur, adresse, smtp, port, defaut,
       connexionAuthentifiee, startTLS, utilisateur, parametres
FROM adresses_mail;
```

Preuve attendue : aucun hôte, domaine ou paramètre Connecthys. Les éventuelles références SMTP/Mailjet sont classées séparément.

#### Table `sauvegardes_auto`

```sql
SELECT * FROM sauvegardes_auto;
```

Puis inspecter le schéma si nécessaire (`DESCRIBE sauvegardes_auto;` sous MySQL ou `PRAGMA table_info(sauvegardes_auto);` sous SQLite) afin d'identifier destinations, e-mails, réseau et conditions d'exécution.

Preuve attendue : aucune destination, adresse ou ressource Connecthys, et toutes les sauvegardes nécessaires à la sortie sont identifiées.

#### Recherche plus large

Énumérer les tables/colonnes contenant des noms tels que `url`, `host`, `server`, `portail`, `sync`, `token`, `secret`, `login`, `api`, puis examiner les valeurs pertinentes. Adapter la requête au moteur réel ; ne pas lancer un export aveugle de secrets.

### 3.2 Postes Windows

À exécuter sur un poste de recette représentatif, PowerShell en lecture seule sauf pour la phase de blocage contrôlé :

```powershell
schtasks /Query /FO LIST /V | findstr /I "connecthys portail sync http ftp sftp"
Get-CimInstance Win32_Service | Select-Object Name, State, StartMode, PathName
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location, User
Get-ChildItem Env: | Where-Object { $_.Name -match 'CONNECT|PORTAIL|SYNC|API|TOKEN' }
```

Contrôler aussi les clés de démarrage :

```powershell
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
```

Rechercher dans les dossiers d'application et utilisateur connus, en limitant les résultats et sans collecter les valeurs de secrets :

```powershell
$roots = @($env:APPDATA, $env:LOCALAPPDATA, $env:PROGRAMDATA)
Get-ChildItem $roots -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -match '^\.(ini|cfg|conf|json|xml|yaml|yml|txt|log)$' } |
  Select-String -Pattern 'Connecthys|https?://|portail|sync' -CaseSensitive:$false
```

### 3.3 Serveur PMSL35

Contrôler uniquement ce qui existe réellement aujourd'hui : services, tâches, règles pare-feu, DNS, scripts, montages/partages et connexions DB. **Ne pas supposer que le service de switch y sera rapatrié.**

Preuves attendues : inventaire des services et tâches avec commande de lancement ; inventaire des flux sortants pertinents ; absence de script/cron/systemd/planification Connecthys ; aucune dépendance DB à une ressource hébergée par Connecthys.

### 3.4 Noethys

Noethys doit être audité séparément car le dépôt Teamworks ne permet pas d'attester son comportement réel. Contrôler paramètres portail/synchronisation, URL/domaines, identifiants/tokens, tâches automatiques, fonctions familles (consultation, réservations, documents, factures/reçus, paiements, informations personnelles, messages, authentification) et logs lors de la coupure.

### 3.5 Messagerie et contenus distribués

Rechercher dans les modèles d'e-mail, signatures, courriers, PDF, documents partagés, raccourcis, favoris administratifs, QR codes et pages d'accueil : `Connecthys`, anciennes variantes, domaines contractuels Connecthys une fois identifiés et anciennes URL de portail.

Preuve négative : inventaire daté et zéro URL encore distribuée.

### 3.6 Contrat et RGPD

À vérifier avec la personne responsable du contrat / DPO : date d'échéance et préavis ; modalités de résiliation ; restitution/export complet des données ; format et lisibilité de l'export ; durée de disponibilité après résiliation ; suppression chez le prestataire et sous-traitants ; preuve de suppression si requise ; traitements/sous-traitants à retirer du registre RGPD ; comptes techniques et droits à révoquer **après** validation de la coupure.

---

## 4. Test de coupure contrôlée

### 4.1 Préparation

1. Utiliser **un poste de recette**, jamais un poste de production isolé sans plan de retour arrière.
2. Sauvegarder la configuration locale et la base de recette.
3. Vérifier une restauration avant la coupure.
4. Identifier les **domaines/IP exacts** de Connecthys à partir du contrat, des DNS, de la base/configuration et d'une capture réseau de référence.
5. Établir une liste d'autorisation des autres services nécessaires (DB PMSL35, SMTP/Mailjet si utilisé, GitHub/update, références réglementaires, etc.).
6. Démarrer la collecte des logs Teamworks/Noethys et, si possible, une capture réseau filtrée sur le processus ou les domaines ciblés.

### 4.2 Blocage

Bloquer **uniquement** les domaines/IP confirmés Connecthys. Préférer une règle pare-feu/DNS de recette réversible. Ne pas utiliser un blocage Internet global, qui rendrait le résultat ambigu.

Documenter avant application : règle ajoutée, cible, heure de début et commande de suppression/rollback.

### 4.3 Parcours Teamworks à exécuter

1. lancement Teamworks et ouverture de la base ;
2. ouverture/consultation individus ;
3. création/modification d'un individu de recette ;
4. consultation et modification de présences ;
5. recrutement/candidatures ;
6. création/consultation d'un contrat de recette ;
7. génération PDF / impression représentative ;
8. export représentatif ;
9. sauvegarde manuelle ;
10. déclenchement ou simulation d'une sauvegarde automatique applicable au poste ;
11. restauration sur copie de recette ;
12. envoi d'e-mail de recette si la messagerie fait partie des usages attendus ;
13. ouverture des préférences/configurations principales ;
14. ouverture de l'updater sans installer de mise à jour ;
15. fermeture puis redémarrage de Teamworks.

### 4.4 Parcours Noethys à exécuter

1. lancement et authentification ;
2. consultation dossiers/familles ;
3. réservations ;
4. documents ;
5. factures/reçus ;
6. paiements si applicable ;
7. informations personnelles ;
8. messages ;
9. fonctions portail/synchronisation visibles ;
10. fermeture/redémarrage et observation des tâches de fond.

### 4.5 Observation

Pendant tout le test : surveiller les logs applicatifs et erreurs UI ; relever les tentatives DNS/TCP/HTTP vers les cibles bloquées ; surveiller Planificateur et services ; attendre au moins un créneau où une sauvegarde/tâche automatique configurée devrait se déclencher ; distinguer une erreur Connecthys d'une erreur provoquée par un autre service externe.

### 4.6 Retour arrière

1. Supprimer les règles de blocage.
2. Purger le cache DNS si nécessaire.
3. Vérifier que les services habituels sont de nouveau joignables.
4. Réexécuter un parcours court de référence.
5. Archiver les logs/captures et la chronologie.

### 4.7 Qualification des résultats

Pour chaque erreur, enregistrer : heure, application, parcours, message, endpoint tenté, caractère reproductible, criticité, contournement, lien ou non avec Connecthys.

Une coupure est **concluante négativement** seulement si aucun flux Connecthys nécessaire n'est observé et si tous les parcours critiques restent fonctionnels.

---

## 5. Critère de sortie

La résiliation ne peut être déclarée techniquement prête que lorsque toutes les preuves suivantes existent :

- **zéro flux Connecthys nécessaire** pendant la recette de coupure ;
- **zéro tâche automatique Connecthys nécessaire** ;
- **zéro service/démarrage Connecthys nécessaire** ;
- **zéro secret ou compte Connecthys nécessaire** ;
- **zéro URL Connecthys encore distribuée** ;
- **données nécessaires récupérées et lisibles** ;
- **restauration validée** ;
- **Teamworks et Noethys validés pendant la coupure contrôlée** ;
- **aucun blocage administratif/contractuel/RGPD**.

Tant qu'un de ces points n'est pas démontré, le verdict reste **CONNECTHYS : NON DÉMONTRÉ**. Si un besoin actif est confirmé, il devient **CONNECTHYS : NON PRÊT**. Ce n'est qu'après validation de tous les critères que le verdict peut devenir **CONNECTHYS : PRÊT À RÉSILIER**.

---

## 6. Tableau de sortie Connecthys

| Contrôle | Emplacement | Preuve attendue | Responsable | Statut |
| --- | --- | --- | --- | --- |
| Code : référence Connecthys exécutable | Dépôt Git | Scanner + revue sémantique ; zéro référence exécutable | Dev | En cours |
| Code : résidu updater | `teamworks/Dlg/DLG_Updater.py` | Qualification du bloc `ctrl_serveur_portail` comme mort ou preuve d'un appel réel | Dev | Conforme |
| Configuration applicative | Fichiers + table `parametres` | Zéro URL/option Connecthys | PMSL35 + Dev | À faire |
| Base réelle | DB Teamworks/Noethys | Requêtes datées, résultat qualifié | Admin DB | À faire |
| Tâches planifiées Windows | Postes + serveur | Export `schtasks`, zéro tâche Connecthys nécessaire | Admin système | À faire |
| Services / démarrage | Windows + serveur | Inventaire services/startup, zéro Connecthys | Admin système | À faire |
| Sauvegardes automatiques Teamworks | `sauvegardes_auto` + postes | Toutes destinations qualifiées, aucune Connecthys | PMSL35 + Dev | À faire |
| Scripts externes | Postes + serveur | Recherche ciblée, zéro script Connecthys actif | Admin système | À faire |
| Trafic réseau | Poste de recette | Capture pendant parcours ; zéro flux Connecthys nécessaire | Admin réseau | À faire |
| DNS / pare-feu | Infra | Liste exacte des domaines/IP Connecthys | Admin réseau | À faire |
| Logs | Teamworks, Noethys, OS | Aucun échec Connecthys pendant coupure | PMSL35 + Dev | À faire |
| Comptes / secrets | DB, fichiers, coffre éventuel | Inventaire sans valeur secrète ; zéro secret Connecthys nécessaire | Admin + DPO | À faire |
| Messagerie | `adresses_mail`, serveur mail | Hôtes qualifiés ; aucun relais Connecthys | Admin messagerie | À faire |
| Liens utilisateurs | E-mails, courriers, PDF, QR, raccourcis | Zéro URL Connecthys distribuée | Métier / Communication | À faire |
| Documentation | Dépôt + docs internes | Historique identifié ; aucune instruction active vers Connecthys | Dev + Métier | En cours |
| Sauvegarde/export des données | Connecthys + DB | Export complet, horodaté, lisible | PMSL35 | À faire |
| Restauration | Environnement de recette | Restauration réussie et vérifiée | PMSL35 + Dev | À faire |
| Test de coupure | Poste de recette | Procès-verbal de recette + logs + capture | PMSL35 + Dev | À faire |
| Recette métier Teamworks | Poste de recette | Parcours critiques validés | Référent métier | À faire |
| Recette métier Noethys | Poste de recette | Parcours critiques/portail validés | Référent métier | À faire |
| RGPD | Registre / contrat / DPA | Sort des données et sous-traitants validé | DPO / Direction | À faire |
| Échéance contractuelle | Contrat Connecthys | Date, préavis, procédure et coûts confirmés | Direction / Admin | À faire |

---

## 7. Outil d'audit reproductible

### Commandes

Inventaire complet :

```bash
python tools/audit_connecthys.py . --json audit-connecthys.json --markdown audit-connecthys.md
```

Tests ciblés :

```bash
python -m pytest -q tests/test_audit_connecthys.py
```

Suite du dépôt :

```bash
python -m pytest -q
```

Le scanner inventorie : marque Connecthys, URL, primitives réseau, synchronisation/portail, secrets/identifiants, automatisation, stockage de configuration et imports/exports. Les catégories génériques produisent des **candidats**, jamais des dépendances Connecthys confirmées automatiquement.

### Politique de garde

- une nouvelle référence explicite Connecthys en code exécutable est bloquante ;
- une référence historique dans un commentaire/document est inventoriée mais n'est pas automatiquement bloquante ;
- les URL et mots génériques (`sync`, `portal`, `remote`, etc.) sont revus sémantiquement ;
- aucune énorme liste arbitraire de chaînes n'est utilisée comme critère de CI.

---

## 8. Validation exécutée et limites

### Exécuté

Premier passage CI Linux sur la PR d'audit :

- workflow unique : succès ;
- compilation Python : succès ;
- politique UTF-8 : succès ;
- composants essentiels : succès ;
- audit des risques runtime : succès ;
- contrôle chemins SQLite binaires : succès ;
- contrôle branches Phoenix : succès ;
- inventaires mutables/imports/compilation : succès ;
- `pytest` : **2 011 réussis, 3 ignorés, 1 échec** ;
- l'unique échec était le test Connecthys ajouté, qui a correctement révélé le commentaire historique de `DLG_Updater.py` et déclenché l'analyse sémantique décrite ci-dessus.

Le test a ensuite été corrigé pour distinguer commentaire historique et référence exécutable. La CI de ce commit doit être consultée avant de considérer la PR validée.

### Non exécuté / non accessible depuis cet audit

- aucun poste Windows réel PMSL35 inspecté ;
- aucune base de production/réelle interrogée ;
- aucun serveur PMSL35 inspecté ;
- aucun Planificateur de tâches réel inspecté ;
- aucun DNS/pare-feu réel modifié ;
- aucune capture réseau d'un usage réel ;
- aucun environnement Noethys réel inspecté ;
- aucune coupure Connecthys exécutée ;
- aucun contrat, facture, DPA/RGPD ou espace client Connecthys consulté ;
- aucune donnée Connecthys exportée/restaurée.

Ces limites sont précisément la raison du verdict **NON DÉMONTRÉ**.
