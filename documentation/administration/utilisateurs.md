# Utilisateurs et habilitations

## Ce qui est réellement disponible aujourd'hui

Teamworks-CCNS **ne propose pas de gestion de comptes applicatifs avec rôles/permissions**. Deux mécanismes bien plus limités existent réellement :

- **Comptes réseau MySQL** (`Paramétrage > Accès réseau`) : gèrent la connexion à un serveur MySQL partagé, pas des comptes utilisateurs de l'application elle-même.
- **Protection par mot de passe du dossier** (`Paramétrage > Protection par mot de passe`) : protège l'ouverture d'un dossier local ou réseau, sans notion d'utilisateur nommé ni de rôle.

Ne confondez pas ces deux mécanismes avec une gestion d'habilitations par utilisateur.

## Chantier en cours, non branché à l'application

Le dépôt contient un modèle de domaine pour une future gestion d'habilitations (`domain/access/`, `domain/security/`, `application/security/`) : comptes, rôles, portées d'accès, service d'autorisation, historique des accès sensibles.

!!! danger "Ne pas présenter comme disponible"
    Ce modèle est **entièrement en mémoire, sans persistance ni interface graphique branchée**. Il n'est appelé par aucun écran de `teamworks/` (wxPython) ni par `GestionDB`. La documentation interne du projet le confirme explicitement : la persistance, l'interface graphique et le filtrage fin restent à faire. Niveau de maturité réel : **expérimental / prévu**, pas disponible pour un utilisateur final.

## Voir aussi

[Paramétrage](parametrage.md) · [Données, sauvegardes et MySQL](donnees-sauvegardes.md) · [Organisation du dépôt](../developpement/organisation-depot.md)
