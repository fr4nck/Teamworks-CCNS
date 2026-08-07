# Maintenance Teamworks-CCNS

**Mise à jour : 7 août 2026**

## Statut du document

Ce document **n’est plus une roadmap**.

Depuis TW-126 / PR #196, **`ROADMAP.md` à la racine est l’unique feuille de route du projet**. Les états des lots `TW-*`, l’ordre des travaux, les critères de maturité et le prochain jalon doivent être maintenus uniquement dans `ROADMAP.md`.

Ce fichier conserve seulement les principes et priorités techniques de maintenance à utiliser lorsqu’un lot est décidé dans la roadmap officielle.

## Documents de référence

| Besoin | Document |
| --- | --- |
| Roadmap officielle et registre récent | `ROADMAP.md` |
| Règles opérationnelles pour agents | `AGENTS.md` |
| Compatibilité réellement exercée | `docs/MATRICE_COMPATIBILITE.md` |
| Politique CI | `docs/CI_POLICY.md` |
| Règles de performance | `docs/34-performance.md` |
| Audit des performances | `docs/AUDIT_PERFORMANCES.md` |
| Pérennité, dépendances et refontes | `docs/35-perennite-technique.md` |
| Architecture et évolution long terme | `docs/ARCHITECTURE_EVOLUTION.md` |
| Cartographie fonctionnelle et technique | `docs/30-cartographie-teamworks-ccns.md` |

## Principes de maintenance

Toute intervention de maintenance doit rester :

- mesurée et reliée à un défaut ou un besoin réel ;
- compatible avec le socle historique tant qu’une migration explicite n’est pas décidée ;
- réversible lorsque la base, le packaging ou les dépendances sont concernés ;
- couverte par un test ciblé ou une vérification reproductible ;
- frugale côté GitHub Actions ;
- cohérente avec l’unique workflow `.github/workflows/ci.yml` ;
- documentée dans `ROADMAP.md` si elle modifie l’ordre des travaux ou le niveau de maturité.

## Priorités techniques permanentes

### 1. Fiabilité Windows

Avant les refontes :

- démarrage ;
- ouverture d’une base existante ;
- dialogues et listes principales ;
- sauvegarde / restauration ;
- exports ;
- fermeture propre ;
- diagnostic exploitable en cas d’erreur.

### 2. Compatibilité des données historiques

Les correctifs doivent éviter toute migration destructive implicite. Les dates, encodages et anciennes configurations sont normalisés à leurs frontières de lecture/écriture.

### 3. CI frugale et reproductible

La CI actuelle est volontairement consolidée :

- un seul workflow ;
- Python 3.11 comme référence actuelle ;
- Ubuntu 24.04 pour tests et audits ;
- Windows Server 2022 pour les parcours critiques ;
- build Windows uniquement sur demande explicite ou tag de version.

Aucun workflow concurrent ne doit être ajouté pour un contrôle qui peut rejoindre le pipeline existant.

### 4. Packaging

Le packaging doit rester reproductible, vérifier son contenu et produire des empreintes d’intégrité. Toute dépendance dynamique ou ressource indispensable doit être explicitement couverte.

### 5. Performance

Ne pas optimiser sur intuition. Mesurer avant/après sur un parcours représentatif :

- connexion ;
- SQL ;
- fetch ;
- transformation Python ;
- construction / rafraîchissement wxPython ;
- temps total perçu.

### 6. Architecture

Préférer :

- un correctif local quand le défaut est local ;
- une mutualisation progressive lorsque plusieurs écrans dupliquent la même lecture ou la même règle ;
- une refonte dédiée seulement lorsque les correctifs locaux deviennent nombreux, risqués et incohérents.

## Critère d’acceptation d’un lot de maintenance

Un lot est exploitable s’il fournit :

1. un problème ou objectif précis ;
2. une modification limitée au périmètre utile ;
3. une preuve automatique ou manuelle adaptée ;
4. une analyse de compatibilité si Python, OS, base, réseau, dépendances ou packaging sont concernés ;
5. une limite connue et un retour arrière pour les changements risqués ;
6. une mise à jour de `ROADMAP.md` si le lot modifie l’état réel du projet.

## Note sur les identifiants TW

L’historique contient des collisions anciennes (`TW-123`, `TW-126`, `TW-138`, `TW-139`). Elles sont documentées dans `ROADMAP.md` et ne doivent pas être corrigées rétroactivement.

Avant de créer un nouveau lot, vérifier qu’un identifiant n’existe pas déjà dans une branche, un commit, une issue ou une PR.
