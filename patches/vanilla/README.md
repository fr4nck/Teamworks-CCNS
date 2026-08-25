# Backports Teamworks Vanilla

Ces patches sont destinés au socle original Teamworks 2.1.3.1, base commune :

`00bd52ef85853eb617361a15c2f0cc0cfa1b898e`

Ils ne contiennent ni migration Python 3/Phoenix, ni thème moderne, ni CCNS.

## Patches préparés

- `VFIX-001-002-sauvegardes.patch` — dossiers sources absents + grilles de sauvegarde ;
- `VFIX-003-gadgets.patch` — sélection et bornes de déplacement ;
- `VFIX-004-apercu-email.patch` — navigation hors limites ;
- `VFIX-005-boutons-image.patch` — tolérance aux ressources image absentes.

## Application

Depuis la racine d'une copie propre de Teamworks 2.1.3.1 :

```bash
git apply --unidiff-zero patches/vanilla/VFIX-001-002-sauvegardes.patch
git apply --unidiff-zero patches/vanilla/VFIX-003-gadgets.patch
git apply --unidiff-zero patches/vanilla/VFIX-004-apercu-email.patch
git apply --unidiff-zero patches/vanilla/VFIX-005-boutons-image.patch
```

Le format à contexte nul est volontaire : les sources Vanilla historiques sont en `iso-8859-15` et les patches ne doivent pas provoquer une conversion globale d'encodage des fichiers.

## Validation déjà effectuée

Sur une copie exacte du snapshot Vanilla fourni :

- les quatre patches passent `git apply --unidiff-zero --check` ;
- les quatre patches s'appliquent sans conversion d'encodage ;
- les quatre fichiers modifiés passent la compilation Python (`py_compile`) ;
- `git diff --check` est propre après application.

Cette validation est **statique**. Elle ne remplace pas un démarrage réel de Teamworks dans son environnement historique ni le test manuel des quatre parcours concernés.

## Règle

Tout nouveau patch ajouté ici doit d'abord être confirmé dans `Noethys/Teamworks`, rester minimal et être classé dans `docs/01_VANILLA_BUGFIX.md`.
