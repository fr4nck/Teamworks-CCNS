# DPAE et DUE

Teamworks-CCNS wx contient un module historique d’**édition DUE/DPAE** (`DLG_Edition_DUE.py`) qui construit un formulaire PDF à partir des données employeur et salarié.

## Nature du module

Le module ne passe pas par le moteur générique `{MOTCLE}`. Il définit ses propres champs de formulaire, ses catégories (« Établissement employeur », « Futur salarié », « Autres éléments ») et des coordonnées de rendu PDF.

On y trouve par exemple des identifiants internes comme `NUM_SIRET`, `CODE_APE`, `DENOMINATION`, `CIVILITE_SALARIE`, `NUMSECU_SALARIE` ou `DATENAISS_SALARIE`.

> Ces identifiants **ne sont pas des mots-clés de publipostage** et ne doivent pas être saisis comme `{NUM_SIRET}` dans un modèle Teamword/Word/Writer sans autre preuve d’exposition.

## Utilisation

Le parcours fonctionnel exact dépend du point d’entrée contrat/DUE de l’interface. Avant validation, contrôlez toutes les données employeur, l’identité du salarié, la naissance, la nationalité et les éléments de contrat présentés dans le formulaire.

Le rendu est produit par ReportLab et place les valeurs dans les cases du document.

## DPAE / DUE et publipostage

Il n’existe pas de contexte `dpae` dans `UTILS_Publipostage_donnees.py`. Les documents contractuels génériques peuvent néanmoins utiliser les vraies balises Contrat/Individu lorsqu’ils sont lancés depuis le contexte Contrat : voir [[Contrats, CCNS et CEE]] et [[Mots-clés de publipostage]].

## État à valider

Le module est présent dans le code et ses champs sont réels. Le parcours de validation administrative « DPAE moderne » doit cependant être confirmé fonctionnellement sur la version livrée avant de présenter l’édition PDF historique comme équivalente à une télétransmission officielle.
