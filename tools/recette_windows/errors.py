class RecipeError(RuntimeError):
    """Erreur de recette qui doit produire un diagnostic exploitable."""


class BlockedEnvironment(RecipeError):
    """Une précondition empêche la recette de qualifier Teamworks."""


class UnsupportedRunner(BlockedEnvironment):
    """Le runner ne fournit pas un bureau Windows interactif."""


class DestructiveDialogDetected(RecipeError):
    """Une confirmation destructive a ete detectee avant toute validation."""
