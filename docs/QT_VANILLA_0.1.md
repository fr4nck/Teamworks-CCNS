# Qt Vanilla 0.1 — contrat de release

## But

Qt Vanilla 0.1 est la première version Qt de référence installable de Teamworks-CCNS. Elle ne cherche pas la parité complète avec la Vanilla wx. Elle doit fournir un sous-ensemble cohérent, qualifié et exploitable sans environnement de développement.

Version cible : `0.1.0`.

Tag cible : `qt-v0.1.0`.

## Fonctions incluses

- application native PySide6 sous Windows ;
- liste, recherche et sélection des individus ;
- Généralités en lecture ;
- Contrats en lecture ;
- création CDI/CDD CCNS dans le périmètre déjà qualifié ;
- modification et suppression transactionnelles des contrats dans le périmètre qualifié ;
- Signature et DUE ;
- Présences en lecture ;
- Scénarios en lecture ;
- Frais : déplacements et remboursements avec CRUD transactionnel et rattachement/détachement ;
- Documents RH : préparation du contexte, catalogue des modèles, compatibilité, états et erreurs ;
- modèles `.doc`, `.odt`, `.twd` détectables statiquement ;
- SQLite/MySQL via les adaptateurs qualifiés ;
- erreurs métier structurées et relecture après écritures.

## Exclusions explicites

Ne font pas partie du contrat 0.1 :

- Planning graphique complet ;
- drag/drop planning ;
- écriture Présences depuis Qt ;
- CRUD Scénarios depuis Qt ;
- création CEE complète ;
- renouvellement avancé de contrat ;
- édition complète des classifications/valeurs de point historiques ;
- édition des Généralités ;
- recrutement complet ;
- génération Word/COM ;
- génération LibreOffice/UNO ;
- impression ou conversion PDF des Documents RH ;
- cache auxiliaire historique `distances` ;
- parité complète avec la wx.

Une fonction exclue doit être absente, clairement désactivée ou présentée comme consultation/préparation. Elle ne doit jamais simuler un succès.

## Rails requis avant le tag

Le SHA de release doit intégrer proprement les lots qualifiés nécessaires de :

- PR #431 — socle Qt et Contrats ;
- PR #444 — Frais ;
- PR #453 — Documents RH ;
- les lectures Présences/Scénarios déjà qualifiées dans le socle.

Les services non raccordés à l'UI ne deviennent pas automatiquement des fonctions de la Vanilla.

## Runtime

La Qt Vanilla 0.1 ne dépend pas de wxPython pour démarrer.

Le runtime autorisé inclut notamment :

- Python embarqué par PyInstaller ;
- PySide6 / Qt ;
- mysql-connector-python ;
- les dépendances Python métier nécessaires ;
- les ressources statiques Teamworks utiles au périmètre 0.1.

Le runtime ne doit pas contenir :

- wxPython ;
- Word ou LibreOffice embarqués ;
- base utilisateur ;
- configuration utilisateur ;
- secrets ou identifiants MySQL ;
- données de production.

## Artefacts Windows

### Portable

Nom :

`Teamworks-CCNS-Qt-0.1.0-windows-x64-portable.zip`

Contenu fonctionnel :

- `Teamworks-CCNS-Qt.exe` ;
- runtime Python/Qt et dépendances ;
- ressources `Static/` nécessaires ;
- modèles Documents RH ;
- `VANILLA_VERSION.txt` ;
- dossier vide `Portable/`.

La présence de `Portable/` force l'isolation des réglages et données du portable par rapport au profil Windows habituel.

### Installateur

Nom :

`Teamworks-CCNS-Qt-0.1.0-windows-x64-setup.exe`

L'installateur :

- s'installe dans `Program Files\Teamworks-CCNS-Qt` ;
- utilise un AppId distinct de la Vanilla wx ;
- peut coexister avec la wx ;
- crée uniquement les fichiers applicatifs et raccourcis ;
- fournit un désinstalleur ;
- n'installe jamais le dossier `Portable/` ;
- ne crée, ne migre, ne déplace et ne supprime aucune base utilisateur.

### Sommes de contrôle

`SHA256SUMS.txt` doit contenir les SHA-256 du ZIP portable et du setup.

## Critères de sortie

La version ne peut recevoir le tag stable `qt-v0.1.0` que si le même SHA satisfait tous les points suivants :

1. CI Qt Linux verte ;
2. CI Qt Windows native verte ;
3. workflow Packaging Qt Vanilla vert ;
4. build réalisé dans un environnement où wxPython n'est pas installé ;
5. aucun artefact wx détecté dans le dossier PyInstaller ;
6. smoke du runtime figé réussi ;
7. compilation Inno Setup réussie ;
8. installation silencieuse CI réussie ;
9. lancement de l'installation CI réussi ;
10. désinstallation CI réussie ;
11. recette Windows manuelle réussie ;
12. recette sur la version MySQL réellement déployée réussie ;
13. recette sur copie représentative de données réussie ;
14. aucune mutation de schéma déclenchée par une simple lecture ;
15. portable et setup produits depuis le même SHA ;
16. limites connues documentées.

Une CI verte seule ne suffit pas à déclarer la Vanilla 0.1.
