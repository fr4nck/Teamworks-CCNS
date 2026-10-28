# QT-DOC-06R - Apercu TWD integre

Date : 2026-10-28
Base : d2bdebf9
Branche : qt/integration-document-core

## Integration

- Core documentaire adopte au commit 8a9b644.
- Contexte de publipostage expose au dialogue Qt.
- Selection et apercu des modeles TWD.
- Remplacement des champs connus.
- Signalement des champs non resolus.
- Affichage des images integrees.
- Aucun lancement Office.
- Aucune ecriture dans les modeles sources ou la base.

## Tests locaux

- Compilation Python : PASS.
- Tests documentaires et Qt cibles : PASS.
- Smoke Qt Windows natif : PASS.

## Gates restants

- CI GitHub Linux et Windows.
- Recette avec copie de base reelle.
- Verification visuelle des documents complexes.
- Aucune fusion automatique vers qt/master.


## QT-DOC-07 et QT-DOC-08 : preuves visuelles et avertissements

- QT-DOC-07 : les captures avec \`QT_QPA_PLATFORM=offscreen\` affichaient
  des glyphes carrés ; le texte source et les images étaient conservés.
- QT-DOC-07B : les aperçus Windows natifs et Segoe UI sont lisibles.
  Les paramètres de rendu et de police ont changé ensemble ; la cause
  élémentaire reste à isoler si une capture offscreen est exigée.
- QT-DOC-08 : les champs canoniques connus mais absents sont signalés
  séparément des variables historiques non mappées (NBREJOURS,
  REPARTITION, BRUTJOUR). Les exemples sont explicitement non validés
  pour signature.
- Le module documentaire ne génère, n'enregistre et n'imprime aucun document.
  Le contrat de sortie \`clé connue vide → vide\` reste à certifier
  **avant** toute activation future de génération.
- Les clauses et dates fixes des fichiers historiques d'exemple ne sont pas
  des contenus contractuels validés ; CEE et CDD requièrent un audit métier.
- La recette Windows avec une copie représentative de base et de MySQL
  reste obligatoire avant toute fusion.

## QT-DOC-08C - Contraste de l'aperçu en theme sombre

- Recette Windows native sur les deux premiers exemples : ouverture, bandeau
  de non-validite et fusion corrects, mais texte noir sur fond gris fonce.
  Verdict visuel KO malgre la validation automatique precedente.
- Correction isolee dans QTextBrowser : fond du document blanc, texte par
  defaut sombre, selection lisible et marge de page de 16 px. Le reste de
  l'interface conserve son theme, sans changement du moteur TWD.
- Test GUI : la fenetre parente impose volontairement une feuille de style
  sombre ; controle de la palette du document et d'un pixel reel de la
  surface peinte. Le pilote Windows verifie les memes invariants et les
  enregistre dans report.json.
- Gate : la recette graphique des six documents doit etre rejouee apres
  publication ; aucune fusion avant validation du nouveau HEAD et de la
  recette sur base representative.
