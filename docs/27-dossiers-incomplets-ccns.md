# Extension CCNS de la fenêtre Dossiers incomplets

Cette étape cible explicitement la fenêtre globale de supervision par individu.

## Ce qui est ajouté

- génération de nœuds CCNS à rattacher sous chaque individu ;
- helper de style pour distinguer :
  - bloquant
  - à revoir
  - ok
- helper d'ouverture :
  - ouverture directe du contrat s'il n'y en a qu'un ;
  - sinon bascule conseillée vers la fiche individuelle / Synthèse CCNS.

## Logique retenue

La fenêtre **Dossiers incomplets** devient :
- le point d'entrée global ;
- la fiche individuelle devient :
- le point de détail.

## Nœuds CCNS proposés

- `X alerte(s) CCNS bloquante(s)`
- `X contrat(s) CCNS à revoir`
- `X contrat(s) CCNS sans anomalie détectée`
- `Synthèse CCNS : ...`

## Pourquoi c'est cohérent

On s'appuie sur un écran déjà existant, déjà centré sur l'individu, déjà utilisé comme tableau d'appel.
