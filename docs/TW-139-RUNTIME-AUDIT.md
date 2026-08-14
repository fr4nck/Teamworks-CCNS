# TW-139 — Audit et stabilisation des parcours runtime

## Objectif

Obtenir une navigation sans traceback sur les écrans principaux de Teamworks avant toute nouvelle fonctionnalité ou refonte visuelle.

## Environnement de référence

- Windows 10 AMD64
- Python 3.11
- wxPython 4.2.5, avec préparation de la compatibilité 4.3
- base Teamworks historique existante

## Parcours de recette

| Écran | Ouverture | Chargement | Ajout | Modification | Suppression | Fermeture | Résultat |
|---|---:|---:|---:|---:|---:|---:|---|
| Accueil | ✓ | ✓ | N/A | ✓ | N/A | ✓ | Validé 30/07/2026 |
| Individus | ✓ | ✓ | ☐ | ☐ | ☐ | ✓ | Partiellement validé — recette ajout/modif/suppr requise |
| Présences | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Recrutement | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Contrats | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Frais | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ | À tester |
| Paramètres | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |
| Rapports | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |
| Impression | ☐ | ☐ | N/A | ☐ | N/A | ☐ | À tester |

## Corrections appliquées dans cette PR

### Lot 1 — Gardes résultats SQL vides

| Fichier | Méthode | Symptôme |
|---|---|---|
| `CTRL_Page_generalites.py` | `__init__` | `TypeError` si France absente de la table `pays` |
| `CTRL_Page_generalites.py` | `Importation` | `IndexError` si personne supprimée |
| `CTRL_Page_generalites.py` | `SetPaysNaiss`, `SetNationalite` | `TypeError` si pays inexistant |
| `CTRL_Personnes.py` | `OnSelectPersonne` | `IndexError` si personne supprimée |
| `CTRL_Recrutement.py` | `MAJidentite` | `IndexError` si candidat/personne supprimé |
| `DLG_Saisie_candidat.py` | `Importation` | `IndexError` si candidat supprimé |
| `DLG_Saisie_coords.py` | `Importation` | `IndexError` si coordonnée supprimée |
| `DLG_Saisie_piece.py` | `Importation` | `IndexError` si pièce supprimée |
| `DLG_Saisie_presence.py` | `ImportDonneesModif` | `IndexError` si présence supprimée |
| `DLG_Importation_vacances.py` | `ImportationZone` | `IndexError` si organisateur absent |
| `DLG_Parametres_calendrier.py` | `Importation`, `OnLeftLink` | `IndexError` si gadget absent |
| `DLG_Saisie_champs_contrats.py` | `Importation` | champs NULL provoquant une erreur de formatage |
| `CTRL_Photo.py` | `OnBoutonPhoto`, `OnMenuPhoto` | `IndexError` si personne supprimée |

### Lot 2 — Assertion wxWidgets

| Fichier | Problème | Correction |
|---|---|---|
| `DLG_Selection_periode.py` | `wx.ALIGN_RIGHT` dans 4 sizers horizontaux | drapeau retiré des appels `.Add()` |

### Lot 3 — Paramètres du dossier et du calendrier

| Fichier | Méthode | Correction |
|---|---|---|
| `DLG_Parametres_dossiers.py` | `Importation`, `OnLeftLink` | gardes + fermeture DB avant retour |

### Lot 4 — Gardes `ResultatReq()[0]` restantes (01/08/2026)

| Fichier | Méthode | Correction |
|---|---|---|
| `DLG_Edition_DUE.py` | `Import_Donnees` | garde contrat/personne + fallbacks classification, type, valeur_point, nationalité, pays_naiss |
| `OL_candidats.py` | `ConvertirFiche` | garde `if not resultats: return` |
| `UTILS_Publipostage_donnees.py` | `Importation_contrat` | fallbacks `if resultats else ""` pour 3 champs |

## Contrôles techniques

- imports et chargement différé des modules ;
- compatibilité wxPython 4.2.5 et 4.3 ;
- ObjectListView : largeur des colonnes, tri, filtrage, rafraîchissement ;
- dates historiques et valeurs absentes ;
- encodage UTF-8 ;
- parentage des widgets et sizers ;
- chemins runtime Windows ;
- absence de blocage de l'interface lors des chargements.

## Tests ciblés TW-139

La PR contient `tests/test_tw139_runtime_guards.py` avec 17 gardes de non-régression. La suite globale du dépôt reste la source de vérité en CI ; aucun job ni workflow supplémentaire n'est ajouté spécifiquement pour TW-139.

## Parcours nécessitant encore une recette Windows manuelle

- Individus > Ajouter (formulaire complet) ;
- Individus > Modifier (avec pays absent) ;
- Présences (ouverture, ajout, modification, suppression) ;
- Recrutement (ouverture fiche candidat, ajout candidature) ;
- Contrats (création, modification) ;
- Frais (saisie, liste) ;
- Paramètres (tous les sous-écrans) ;
- Rapports et Impression.

## Discipline CI

- conserver strictement le workflow unique `.github/workflows/ci.yml` de `master` ;
- les tests TW-139 passent par la suite globale existante ;
- aucun job de détection de chemins ni workflow spécialisé ;
- regrouper les correctifs issus de l'audit dans cette PR unique.

## Critère de fermeture

- aucun traceback connu sur les parcours principaux ;
- CI existante au vert ;
- recette Windows réelle renseignée ;
- aucun nouveau workflow GitHub Actions.

## État technique au 14/08/2026

Aucune occurrence `DB.ResultatReq()[0]` non protégée dans le périmètre audité. Tous les défauts confirmés automatisables de TW-139 sont couverts. La surcouche CI historique de cette branche a été retirée afin d'utiliser exactement le workflow frugal de `master`. La PR reste volontairement en brouillon jusqu'à la recette Windows réelle sur copie de base.
