# Qt Vanilla 0.1 RC — manifeste d'intégration

Branche : `qt/vanilla-0.1-rc`

Cette branche est la première candidate intégrée destinée à devenir la Qt Vanilla 0.1.

## Rails intégrés

- PR #431 — socle Qt / Individus / Contrats / identités stables ;
- PR #444 — Frais transactionnels ;
- PR #453 — Documents RH / publipostage préparatoire ;
- PR #459 — runtime Qt sans wxPython et packaging Windows.

Le rail Frais est intégré avec une ascendance Git explicite dans le commit de fusion de la RC.

## Gates automatiques

La RC doit faire passer, sur le même SHA :

- Validation Qt Linux ;
- Validation Qt Windows native ;
- round-trip MySQL Frais sous MySQL 8 CI ;
- Packaging Qt Vanilla Windows ;
- build sans wxPython ;
- smoke du runtime figé ;
- compilation Inno Setup ;
- installation/lancement/désinstallation ;
- génération des SHA-256.

## Gates réels avant stable

Restent obligatoires avant le tag `qt-v0.1.0` :

- recette Windows sur un poste réel ;
- recette MySQL sur la version réellement déployée ;
- recette sur une copie représentative de la base Teamworks ;
- vérification de coexistence avec la Vanilla wx ;
- absence de mutation de schéma inattendue ;
- validation de la fermeture sans QThread résiduel.

## Documents de recette

- `docs/RECETTE_QT_VANILLA_0.1_WINDOWS.md`
- `docs/RECETTE_QT_VANILLA_0.1_MYSQL_REEL.md`
- `docs/QT_VANILLA_0.1.md`

La RC ne doit pas être fusionnée dans `qt/master` tant que les gates réels ne sont pas signés.
