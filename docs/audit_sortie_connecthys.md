# Audit technique de sortie Connecthys

Date : 5 septembre 2026  
Dépôt : `fr4nck/Teamworks-CCNS`  
Branche : `audit/sortie-connecthys`  
Hors périmètre : PR Qt #366 (`poc/qt-theme-isole`), migration Qt, choix d'hébergement futur du Portail, rapatriement éventuel du service de switch.

> Règle de preuve : **détecté ≠ confirmé**. Une chaîne, une URL, un commentaire ou un mot générique (`sync`, `portail`, `remote`, etc.) n'est pas une dépendance Connecthys active sans suivi sémantique.

## 1. Résumé exécutif

### Verdict

**CONNECTHYS : NON DÉMONTRÉ**

- Dépendance Connecthys trouvée dans le dépôt : **OUI, sous forme de 3 références historiques/documentaires ; aucune dépendance exécutable confirmée**.
- Résiliation techniquement possible aujourd'hui : **NON DÉMONTRÉ**.
- Dépendances Connecthys confirmées dans le code exécuté : **0**.
- Candidats Connecthys actifs non résolus dans le dépôt : **0**.
- Références explicites historiques/documentaires : **3**.
- Principaux bloqueurs restant hors dépôt : **base réelle, postes Windows réels, tâches/services, configuration Noethys, trafic réel, liens distribués, export/restauration des données Connecthys, test de coupure, contrat et RGPD**.

Le dépôt permet donc d'exclure une dépendance Connecthys exécutable identifiable dans Teamworks-CCNS, mais il ne suffit pas à autoriser la résiliation. La décision exige encore les preuves externes et la coupure contrôlée décrites ci-dessous.

### Les 3 références explicites

| Emplacement | Qualification | Preuve |
| --- | --- | --- |
| `ROADMAP.md:9` | **Historique / documentaire** | Connecthys/Portail est cité dans une règle d'architecture, sans appel de code. |
| `docs/00-architecture-cible.md:6` | **Historique / documentaire** | Connecthys apparaît dans la liste des outils connectés, sans logique exécutable. |
| `teamworks/Dlg/DLG_Updater.py:831` | **Historique / morte** | Commentaire « Met en pause le serveur Connecthys si besoin » au-dessus d'un accès à `self.parent.ctrl_serveur_portail.PauseServeur()` ; le parent réel est `Teamworks_core.MyFrame`, qui ne définit pas cet attribut dans la version auditée, et l'exception est absorbée. |

Aucune de ces trois références n'est une dépendance Connecthys exécutable démontrée.

### Prochaines actions prioritaires

1. Identifier les domaines/IP/ports réellement couverts par Connecthys à partir du contrat, des DNS et des configurations réelles.
2. Auditer les tables et paramètres des bases Teamworks/Noethys réelles, sans publier de secrets.
3. Auditer postes Windows, services, démarrages et Planificateur de tâches.
4. Auditer Noethys séparément, y compris portail, synchronisations, tâches, authentification et usages familles.
5. Inventorier toutes les URL encore distribuées aux familles, salariés et administrateurs.
6. Exporter les données nécessaires, vérifier leur lisibilité et valider une restauration.
7. Exécuter le test de coupure contrôlée et conserver logs/captures réseau.
8. Vérifier préavis, restitution/suppression des données et obligations RGPD.

---

## 2. Cartographie

### 2.1 Dépendances et références spécifiques Connecthys

| Emplacement | Type | Appelant | Usage | Criticité | Statut | Remplacement nécessaire |
| --- | --- | --- | --- | --- | --- | --- |
| `ROADMAP.md:9` | Référence documentaire | Aucun | Contexte d'architecture | Nulle à l'exécution | **Historique / documentaire** | Non |
| `docs/00-architecture-cible.md:6` | Référence documentaire | Aucun | Liste d'outils connectés | Nulle à l'exécution | **Historique / documentaire** | Non |
| `teamworks/Dlg/DLG_Updater.py:831` | Résidu portail | `Teamworks_core.MyFrame.On_outils_updater()` instancie `DLG_Updater.Dialog(self)` | Tentative historique de pause d'un serveur portail | Faible ; attribut absent du parent observé et exception absorbée | **Historique / morte** | Non pour la sortie ; nettoyage séparé possible |

### 2.2 Candidats génériques qualifiés

| Emplacement | Type | Usage | Statut | Action restante |
| --- | --- | --- | --- | --- |
| `teamworks/Utils/UTILS_Parametres.py` + table `parametres` | Configuration en base | Valeurs absentes du dépôt pouvant contenir URL/options | **Possible / candidate hors dépôt** | Interroger la base réelle |
| `teamworks/Utils/UTILS_Envoi_email.py` + `adresses_mail` | SMTP/Mailjet + secrets | Envoi de mails | **Externe confirmé, non attribué à Connecthys** | Qualifier hôtes réels, sans publier les secrets |
| `DLG_Config_sauvegarde.py`, `DLG_Saisie_procedure_sauvegarde.py`, `UTILS_Sauvegarde_auto.py`, `sauvegardes_auto` | Tâches automatiques / destinations | Sauvegardes selon jours/heures/postes, destinations hors code possibles | **Possible / candidate hors dépôt** | Examiner les procédures réelles |
| `teamworks/Utils/UTILS_Fichiers.py` / dossier `Sync` | Stockage local | Répertoire nommé Sync | **Candidate générique, non Connecthys** | Examiner un poste réel ; le nom seul n'est pas une preuve |
| `DLG_Updater.py`, `Teamworks_core.py` | HTTP | Mise à jour via `teamworks.ovh` et GitHub | **Externe confirmé, non Connecthys démontré** | Ne pas bloquer lors du test Connecthys sans preuve |
| `application/services/inter_domain_mailbox_client_hr.py` | HTTP sortant / synchronisation | Client configurable | **Candidate générique, non Connecthys** | Contrôler l'endpoint réel |

### 2.3 Ratissage automatisé final

Le scanner final a analysé **1 255 fichiers texte suivis** et écarté **827 fichiers non textuels/non UTF-8**. Il a trouvé :

- **3** références explicites `Connecthys` ;
- **0** référence Connecthys exécutable bloquante ;
- **3** références historiques/documentaires ;
- **96** occurrences d'URL ;
- **67** indices d'API réseau ;
- **103** indices de synchronisation/portail ;
- **299** indices d'automatisation.

Les catégories génériques ont volontairement un rappel large et produisent des **candidats**, pas des dépendances Connecthys. Elles ne doivent pas être additionnées comme un nombre de dépendances.

Le premier prototype de garde avait assimilé le commentaire de l'updater à du code actif et avait donc échoué. Cette alerte a déclenché le suivi d'appels. La garde finale distingue désormais commentaire/documentation et référence exécutable, tout en conservant les traces historiques dans l'inventaire.

---

## 3. Éléments hors dépôt

Aucun contrôle ci-dessous n'est déclaré conforme par hypothèse.

### 3.1 Base réelle

#### Paramètres

```sql
SELECT categorie, nom, parametre
FROM parametres
WHERE LOWER(COALESCE(categorie, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(nom, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%connecthys%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%portail%'
   OR LOWER(COALESCE(parametre, '')) LIKE '%http%';
```

Preuve positive : URL, domaine, identifiant ou option identifiable comme Connecthys.  
Preuve négative : résultat horodaté sans référence Connecthys, puis qualification des paramètres URL/portail restants.

#### Messagerie

Inspecter les métadonnées de `adresses_mail` sans copier de mots de passe, clés ou secrets :

```sql
SELECT IDadresse, moteur, adresse, smtp, port, defaut,
       connexionAuthentifiee, startTLS, utilisateur, parametres
FROM adresses_mail;
```

Preuve attendue : aucun hôte/domaine/paramètre Connecthys. SMTP et Mailjet restent des dépendances externes distinctes.

#### Sauvegardes automatiques

```sql
SELECT * FROM sauvegardes_auto;
```

Inspecter ensuite le schéma si nécessaire pour identifier destinations, e-mails, réseau et conditions d'exécution. Preuve attendue : aucune destination Connecthys et toutes les sauvegardes nécessaires identifiées.

Rechercher plus largement les colonnes/valeurs liées à `url`, `host`, `server`, `portail`, `sync`, `token`, `secret`, `login`, `api`, en adaptant la requête au moteur réel et sans exporter aveuglément des secrets.

### 3.2 Postes Windows

Sur un poste de recette représentatif :

```powershell
schtasks /Query /FO LIST /V | findstr /I "connecthys portail sync http ftp sftp"
Get-CimInstance Win32_Service | Select-Object Name, State, StartMode, PathName
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location, User
Get-ChildItem Env: | Where-Object { $_.Name -match 'CONNECT|PORTAIL|SYNC|API|TOKEN' }
```

Clés de démarrage :

```powershell
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
Get-ItemProperty 'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue
```

Recherche dans les configurations utilisateur, sans collecter de secrets :

```powershell
$roots = @($env:APPDATA, $env:LOCALAPPDATA, $env:PROGRAMDATA)
Get-ChildItem $roots -File -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -match '^\.(ini|cfg|conf|json|xml|yaml|yml|txt|log)$' } |
  Select-String -Pattern 'Connecthys|https?://|portail|sync' -CaseSensitive:$false
```

### 3.3 Serveur PMSL35

Contrôler les services, tâches, DNS/pare-feu, scripts, montages/partages et connexions DB réellement présents. **Ne pas supposer que le service de switch sera rapatrié sur ce serveur.**

Preuve attendue : zéro service/tâche/script/flux Connecthys nécessaire et aucune base dépendante d'une ressource Connecthys.

### 3.4 Noethys

Le dépôt Teamworks ne permet pas d'attester le comportement réel de Noethys. Contrôler séparément : paramètres portail/synchronisation, URL/domaines, comptes/tokens, tâches automatiques, consultation, réservations, documents, factures/reçus, paiements, données personnelles, messages, authentification et logs pendant la coupure.

### 3.5 Liens et usages utilisateurs

Rechercher Connecthys, ses anciennes variantes et ses domaines réels dans : modèles d'e-mails, signatures, courriers, PDF, documents partagés, menus/boutons, aide, raccourcis, favoris administratifs, QR codes, messages automatiques et pages d'accueil.

Preuve négative : inventaire daté et **zéro URL Connecthys encore distribuée**.

### 3.6 Contrat et RGPD

Vérifier : échéance et préavis, procédure/coût de résiliation, restitution/export complet, format et lisibilité, disponibilité après résiliation, suppression chez le prestataire/sous-traitants, preuve de suppression si requise, mise à jour du registre RGPD, puis révocation des comptes techniques seulement après validation de la coupure.

---

## 4. Test de coupure contrôlée

### 4.1 Préparer

1. Utiliser un poste et une base de recette.
2. Sauvegarder la configuration et la base ; valider une restauration avant la coupure.
3. Identifier les **domaines/IP/ports exacts** de Connecthys à partir du contrat, DNS, configuration réelle et capture de référence.
4. Séparer les autres services externes nécessaires : DB PMSL35, SMTP/Mailjet, GitHub/updates, références réglementaires, etc.
5. Démarrer logs Teamworks/Noethys et capture réseau ciblée.

### 4.2 Bloquer

Bloquer **uniquement Connecthys**, via une règle DNS/pare-feu de recette réversible. Ne pas couper Internet globalement. Documenter la règle, la cible, l'heure de début et la commande de rollback.

### 4.3 Parcours Teamworks

Tester au minimum : lancement et ouverture DB ; consultation/création/modification d'un individu ; présences ; recrutement/candidatures ; contrat ; génération PDF/impression ; export ; sauvegarde manuelle ; sauvegarde automatique applicable ; restauration ; e-mail de recette si utilisé ; préférences/configurations ; ouverture de l'updater sans installation ; fermeture et redémarrage.

### 4.4 Parcours Noethys

Tester : lancement/authentification ; dossiers/familles ; réservations ; documents ; factures/reçus ; paiements si applicable ; informations personnelles ; messages ; portail/synchronisation ; fermeture/redémarrage et tâches de fond.

### 4.5 Observer

Pendant le test : logs, erreurs UI, DNS/TCP/HTTP vers les cibles bloquées, services, Planificateur de tâches et créneau d'au moins une tâche automatique réelle. Qualifier toute erreur par application, parcours, endpoint, reproductibilité, criticité et lien démontré ou non avec Connecthys.

### 4.6 Rétablir

Supprimer les règles, purger DNS si nécessaire, vérifier le retour des services habituels, rejouer un parcours court et archiver chronologie/logs/captures.

Une coupure n'est concluante que si **aucun flux Connecthys nécessaire** n'est observé et si tous les parcours critiques restent fonctionnels.

---

## 5. Critère de sortie

La résiliation n'est techniquement prête que lorsque sont démontrés :

- zéro flux Connecthys nécessaire ;
- zéro tâche automatique Connecthys nécessaire ;
- zéro service/démarrage Connecthys nécessaire ;
- zéro secret/compte Connecthys nécessaire ;
- zéro URL Connecthys encore distribuée ;
- données nécessaires récupérées et lisibles ;
- restauration validée ;
- Teamworks et Noethys validés pendant une coupure contrôlée ;
- aucun blocage administratif, contractuel ou RGPD.

Tant qu'un point manque : **CONNECTHYS : NON DÉMONTRÉ**.  
Si un besoin actif est confirmé : **CONNECTHYS : NON PRÊT**.  
Seulement après toutes les preuves : **CONNECTHYS : PRÊT À RÉSILIER**.

---

## 6. Tableau de sortie Connecthys

| Contrôle | Emplacement | Preuve attendue | Responsable | Statut |
| --- | --- | --- | --- | --- |
| Code Connecthys exécutable | Dépôt Git | Scanner + revue sémantique, zéro référence exécutable | Dev | **Conforme** |
| Résidu updater | `teamworks/Dlg/DLG_Updater.py` | Suivi d'appel et qualification | Dev | **Conforme** |
| Documentation dépôt | `ROADMAP.md`, `docs/` | Références historiques identifiées | Dev | **Conforme** |
| Configuration applicative | Fichiers + `parametres` réelle | Zéro URL/option Connecthys | PMSL35 + Dev | **À faire** |
| Base réelle | Teamworks / Noethys | Requêtes datées et résultats qualifiés | Admin DB | **À faire** |
| Tâches planifiées | Postes + serveur | Export et zéro tâche Connecthys nécessaire | Admin système | **À faire** |
| Services / démarrage | Postes + serveur | Inventaire et zéro Connecthys | Admin système | **À faire** |
| Sauvegardes automatiques | `sauvegardes_auto` + postes | Toutes destinations qualifiées | PMSL35 + Dev | **À faire** |
| Scripts externes | Postes + serveur | Recherche ciblée, zéro script actif | Admin système | **À faire** |
| Trafic réseau | Poste de recette | Capture, zéro flux Connecthys nécessaire | Admin réseau | **À faire** |
| DNS / pare-feu | Infra | Liste exacte des cibles Connecthys | Admin réseau | **À faire** |
| Logs | Teamworks, Noethys, OS | Aucun échec Connecthys pendant coupure | PMSL35 + Dev | **À faire** |
| Comptes / secrets | DB, fichiers, coffre | Inventaire sans valeurs secrètes, zéro besoin Connecthys | Admin + DPO | **À faire** |
| Messagerie | `adresses_mail`, serveur mail | Hôtes qualifiés, aucun relais Connecthys | Admin messagerie | **À faire** |
| Liens utilisateurs | E-mails, PDF, QR, raccourcis, pages | Zéro URL Connecthys distribuée | Métier / Communication | **À faire** |
| Export des données | Connecthys + DB | Export complet, horodaté, lisible | PMSL35 | **À faire** |
| Restauration | Recette | Restauration réussie et vérifiée | PMSL35 + Dev | **À faire** |
| Coupure contrôlée | Recette | PV + logs + capture réseau | PMSL35 + Dev | **À faire** |
| Recette Teamworks | Recette | Parcours critiques validés sous coupure | Référent métier | **À faire** |
| Recette Noethys | Recette | Parcours critiques/portail validés sous coupure | Référent métier | **À faire** |
| RGPD | Registre / DPA / contrat | Sort des données et sous-traitants validé | DPO / Direction | **À faire** |
| Échéance contractuelle | Contrat Connecthys | Date, préavis, procédure et coûts confirmés | Direction / Admin | **À faire** |

---

## 7. Audit exécutable

Inventaire :

```bash
python tools/audit_connecthys.py . --json audit-connecthys.json --markdown audit-connecthys.md
```

Garde explicite :

```bash
python tools/audit_connecthys.py . --fail-on-active-brand
```

Tests ciblés :

```bash
python -m pytest -q tests/test_audit_connecthys.py
```

Suite :

```bash
python -m pytest -q
```

Politique : une nouvelle référence explicite Connecthys en code actif non commenté est bloquante ; les références historiques/documentaires restent inventoriées ; les URL et concepts génériques demandent une qualification humaine.

---

## 8. Validation exécutée et limites

### Validation CI du code et des outils d'audit

Sur le commit de code/tests `e16864e51e2a22fed0f21d200e51e4ea71143c29` :

- Linux : compilation Python, politique UTF-8, composants essentiels, audit runtime, contrôles SQLite/Phoenix, inventaires et suite pytest : **succès** ;
- pytest Linux : **2 013 réussis, 3 ignorés, 1 avertissement d'inventaire** ;
- scanner : **1 255 fichiers texte**, **3 références Connecthys**, **0 exécutable bloquante**, **3 historiques/documentaires** ;
- Windows : contrats de dialogues **30 réussis** ;
- Windows : sauvegarde/restauration, checklists, contrat, exports, PDF, navigation, fiche personne, présence, recrutement et aller-retour DB : **succès** ;
- bilan Windows : **tous les contrôles Windows passés**.

Le premier prototype du test Connecthys avait produit un échec volontairement conservateur sur le commentaire de l'updater (`2 011 réussis, 3 ignorés, 1 échec`). Après suivi d'appels, la garde a été corrigée pour ne pas confondre commentaire historique et code exécutable.

### Limites de l'environnement

Non exécuté et donc toujours **À faire** : inspection d'un poste Windows PMSL35 réel ; interrogation d'une base réelle ; inspection du serveur PMSL35 ; Planificateur réel ; DNS/pare-feu réel ; capture réseau réelle ; environnement Noethys réel ; coupure Connecthys réelle ; contrat/facture/DPA/espace client ; export/restauration de données Connecthys.

Ces limites imposent le verdict final :

## **CONNECTHYS : NON DÉMONTRÉ**
