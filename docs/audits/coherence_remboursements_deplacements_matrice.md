# Matrice lecture/écriture — Remboursements ↔ Déplacements

Cette matrice accompagne `coherence_remboursements_deplacements.md`. `R` = lecture, `W` = écriture. La colonne « Source effective » indique la représentation qui décide réellement du comportement du module.

| Module / fonction | Nature | `deplacements.IDremboursement` | `remboursements.listeIDdeplacement` | Source effective | Frontière de commit / transaction | Effet possible d’une divergence |
|---|---|---:|---:|---|---|---|
| `Data/DATA_Tables.py` | Schéma | Déclaration | Déclaration `VARCHAR(300)` | Aucune contrainte d’arbitrage | — | Deux représentations peuvent diverger sans FK/CHECK métier |
| `Dlg/DLG_Gestion_frais.py` — `ListCtrl_personnes.Importation` | Écran gestion globale | R | — | **Clé enfant** | Lecture seule | Personnes et montants classés selon la clé, même si la liste parent dit l’inverse |
| `Ctrl/CTRL_Page_frais.py` — `ListCtrl_deplacements.Importation` | Liste Déplacements | R | — | **Clé enfant** | Lecture seule | Colonne remboursement peut contredire la liste Remboursements voisine |
| `Ctrl/CTRL_Page_frais.py` — `ListCtrl_remboursements.Importation` | Liste Remboursements | — | R | **Liste parent** | Lecture seule | Affiche des IDs rattachés que les autres écrans peuvent considérer libres ou rattachés ailleurs |
| `Dlg/DLG_Saisie_deplacement.py` — `Importation` / `SetRemboursement` | Édition déplacement | R | — | **Clé enfant** | Lecture seule | Une clé orpheline ne résout pas le parent ; le statut peut être masqué visuellement |
| `Dlg/DLG_Saisie_deplacement.py` — `SauvegardeDeplacement` | Écriture déplacement | W (`0`) | — | **Écriture enfant seule** | `ReqInsert/ReqMAJ` committe par défaut puis `Commit()` explicite | Modifier un déplacement remboursé détache la clé sans nettoyer la liste parent |
| `Dlg/DLG_Saisie_remboursement.py` — `SaisieRemboursement.Importation` | En-tête remboursement | — | R, mais non utilisée pour les cases | **Aucune pour le rattachement** | Lecture seule | La chaîne est chargée mais n’est pas la base de reconstruction des rattachements |
| `Dlg/DLG_Saisie_remboursement.py` — `ListCtrl_deplacements.Importation` | Éditeur des rattachements | R | — | **Clé enfant** | Lecture seule | La liste parent peut annoncer des déplacements que l’éditeur ne coche pas |
| `Dlg/DLG_Saisie_remboursement.py` — `Sauvegarde` phase 1 | Création/modification remboursement | — | W | **Liste parent écrite en premier** | Première connexion ; `ReqInsert/ReqMAJ` committe par défaut | Panne avant phase 2 : liste persistée, enfants inchangés |
| `Dlg/DLG_Saisie_remboursement.py` — `Sauvegarde` phase 2 | Rattachement/détachement enfants | W | — | **Clé enfant** | Seconde connexion ; chaque `ReqMAJ` committe par défaut | Panne au milieu : seulement une partie des enfants correspond à la liste parent |
| `Ctrl/CTRL_Page_frais.py` — suppression déplacement | Garde + suppression | R | — | **Clé enfant** | `ReqDEL` committe par défaut | Une liste parent stale n’empêche pas la suppression ; elle peut garder un ID inexistant |
| `Ctrl/CTRL_Page_frais.py` — suppression remboursement, recherche enfants | Garde/suppression | R | — | **Clé enfant** | Lecture puis suppression | Les IDs présents seulement dans la liste parent ne sont pas considérés associés |
| `Ctrl/CTRL_Page_frais.py` — suppression remboursement, `ReqDEL` | Suppression parent | — | Suppression de la ligne entière | **Clé enfant pour retrouver les enfants** | `ReqDEL` committe par défaut avant la libération des enfants | Panne : enfants orphelins vers un parent supprimé |
| `Ctrl/CTRL_Page_frais.py` — suppression remboursement, boucle `ReqMAJ` | Libération enfants | W (`0`) | — | **Clé enfant** | Chaque enfant committe par défaut | Panne partielle : certains enfants libérés, d’autres orphelins |
| `Dlg/DLG_Impression_frais.py` — `ListCtrl.Importation` | Sélection avant impression | R | — | **Clé enfant** | Lecture seule | L’indicateur « Rmbst » suit la clé, pas la liste parent |
| `Dlg/DLG_Impression_frais.py` — `ImpressionFicheFrais` | PDF | R dans la requête, non rendu actuellement | — | **Données déplacement** | Lecture seule | La chaîne parent n’a aucun effet sur le document imprimé |
| `Ol/OL_personnes.py` — `Supprimer` | Garde suppression personne | Pas la relation ; vérifie l’existence de lignes `deplacements` | Pas la relation ; vérifie l’existence de lignes `remboursements` | **Existence des lignes** | Lecture seule | Ne détecte ni ne réconcilie une divergence de rattachement |
| `Ol/OL_personnes_core.py` — suppression personne | Garde suppression personne | Pas la relation ; existence `deplacements` | Pas la relation ; existence `remboursements` | **Existence des lignes** | Lecture seule | Même limite que la version modernisée |

## Lecteurs et supports hors production

| Fichier | Rôle | Observation |
|---|---|---|
| `docs/audit_scenarios_frais_avant_qt.md` | Audit antérieur | Documentait déjà la double représentation et le détachement lors de la modification d’un déplacement |
| `tests/characterisation/test_frais_wx.py` | Caractérisation existante | Vérifie schéma, double écriture, lecteurs différents, suppression et impression ; le défaut de détachement est `xfail(strict=True)` dans le socle |
| `tests/characterisation/test_remboursements_deplacements_coherence.py` | Caractérisation ajoutée par cet audit | Reproduit les états divergents sans importer wxPython |
| `tests/test_expenses_page_modern_ui.py` | Contrats UI | Référence suppression et affichage depuis la clé enfant |
| `tests/test_reimbursement_modern_ui.py` | Contrats UI | Référence le champ `IDremboursement` de l’éditeur |
| `tools/smoke_expenses_lifecycle.py` | Smoke Windows | Vérifie qu’après création normale les deux représentations concordent, mais ne couvre pas les pannes ni le détachement ultérieur |
| `tools/smoke_checklist_controls.py`, `tools/smoke_secondary_checklists.py` | Smokes | Instancient les dialogues, sans définir une autre source de vérité |
| `Static/Databases/Defaut.dat` | Base livrée | 4 déplacements, 1 remboursement, aucune divergence détectée lors de l’audit |
| `Static/Exemples/Exemple_TDATA.dat` | Base d’exemple | 4 déplacements, 1 remboursement, aucune divergence détectée lors de l’audit |

## Synthèse par représentation

### `deplacements.IDremboursement`

Utilisée comme source de décision par :

- gestion globale remboursé/non remboursé ;
- liste Déplacements ;
- affichage du remboursement dans la fiche déplacement ;
- disponibilité et état coché de l’éditeur remboursement ;
- garde de suppression d’un déplacement ;
- recherche/libération des enfants à la suppression d’un remboursement ;
- sélection d’impression.

Elle est écrite par :

- la sauvegarde d’un déplacement, qui la remet à `0` ;
- la sauvegarde d’un remboursement, qui affecte/désaffecte les enfants ;
- la suppression d’un remboursement, qui libère les enfants.

### `remboursements.listeIDdeplacement`

Utilisée comme source métier visible par :

- la colonne « Déplacements rattachés » de la liste Remboursements.

Elle est aussi sélectionnée par l’en-tête de l’éditeur de remboursement, mais l’éditeur ne s’en sert pas pour reconstruire ses cases cochées.

Elle est écrite par :

- la sauvegarde d’un remboursement, avant la phase de mise à jour des enfants.

Cette asymétrie justifie la recommandation de considérer la clé enfant comme source canonique cible et la chaîne parent comme projection de compatibilité.
