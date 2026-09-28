from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class MailMergeRecord:
    """Données publiques d'un document avant enrichissement RH."""

    keywords: tuple[str, ...]
    values: dict[str, object]


MailMergeLoader = Callable[[str, object], tuple[Iterable[str], Mapping[str, object]]]


def _is_public_keyword(value: object) -> bool:
    name = str(value)
    return bool(name) and not name.startswith("_")


def compose_mail_merge_record(
    *sources: tuple[Iterable[str], Mapping[str, object]],
) -> MailMergeRecord:
    """Compose plusieurs sources selon la sémantique historique Teamworks.

    L'ordre des mots-clés est conservé, y compris les doublons éventuels.
    Les clés internes commençant par "_" ne sortent jamais vers les modèles.
    Pour les valeurs, une source placée plus à droite remplace la précédente,
    comme dans le moteur historique personne + contrat/candidature.
    """

    keywords: list[str] = []
    values: dict[str, object] = {}

    for source_keywords, source_values in sources:
        for keyword in source_keywords:
            if _is_public_keyword(keyword):
                keywords.append(str(keyword))
        for keyword, value in source_values.items():
            if _is_public_keyword(keyword):
                values[str(keyword)] = value

    return MailMergeRecord(keywords=tuple(keywords), values=values)


def build_legacy_mail_merge_batch(
    *,
    category: str,
    record_ids: Sequence[object] | None,
    edition_name: str,
    loader: MailMergeLoader,
) -> dict[object, object]:
    """Prépare le contrat de données attendu par le publiposteur wx historique.

    Cette fonction reproduit volontairement le comportement existant :
    la liste de mots-clés du lot est celle du dernier enregistrement chargé
    qui en fournit une. Le format de sortie reste inchangé pour l'adaptateur wx.
    """

    ids = list(record_ids or ())
    result: dict[object, object] = {
        "CATEGORIE": category,
        "NBREDOCUMENTS": len(ids),
        "NOMEDITION": edition_name,
    }

    batch_keywords: list[str] = []
    for index, record_id in enumerate(ids, start=1):
        record_keywords, record_values = loader(category, record_id)
        current_keywords = list(record_keywords or ())
        if current_keywords:
            batch_keywords = current_keywords
        result[index] = dict(record_values or {})

    result["MOTSCLES"] = [(keyword, "base") for keyword in batch_keywords]
    return result
