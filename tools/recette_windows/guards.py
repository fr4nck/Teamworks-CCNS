import re
import unicodedata

from .errors import DestructiveDialogDetected

_DESTRUCTIVE_PATTERNS = (
    "supprim",
    "suppression",
    "effac",
    "detru",
    "destruct",
    "delete",
    "remove permanently",
    "irreversible",
)
_CONFIRMATION_MARKERS = (
    "confirmer",
    "confirmation",
    "souhaitez-vous",
    "voulez-vous",
    "etes-vous",
    "definitiv",
    "irrevers",
    "?",
)


def normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().casefold()


def looks_destructive(texts):
    normalized = " | ".join(normalize_text(text) for text in texts if text)
    return any(token in normalized for token in _DESTRUCTIVE_PATTERNS)


def looks_like_destructive_confirmation(texts):
    values = [normalize_text(text) for text in texts if text]
    for value in values:
        if any(token in value for token in _DESTRUCTIVE_PATTERNS) and (
            "suppression" in value
            or any(marker in value for marker in _CONFIRMATION_MARKERS)
        ):
            return True
    return False


def assert_not_destructive(texts, context="controle"):
    values = [str(text) for text in texts if text]
    if looks_destructive(values):
        raise DestructiveDialogDetected(
            "Action destructive detectee dans %s; aucune validation n'a ete envoyee: %s"
            % (context, " | ".join(values[:8]))
        )


def assert_not_destructive_confirmation(texts, context="fenetre"):
    values = [str(text) for text in texts if text]
    if looks_like_destructive_confirmation(values):
        raise DestructiveDialogDetected(
            "Confirmation destructive detectee dans %s; aucune validation n'a ete envoyee: %s"
            % (context, " | ".join(values[:8]))
        )
