from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.documents import (
    Asset,
    DocumentTemplate,
    HtmlMergeRenderer,
    MergeContext,
)
from infrastructure.documents import import_twd_file


@dataclass(frozen=True)
class TwdPreview:
    html: str
    assets: tuple[Asset, ...]
    warnings: tuple[str, ...]
    unresolved_fields: tuple[str, ...]
    unsupported_features: tuple[str, ...]


def preview_twd_template(
    template: DocumentTemplate,
    context: MergeContext,
) -> TwdPreview:
    """Preview a historical TWD without modifying the source."""
    if not template.location:
        raise ValueError("Missing template path")

    path = Path(template.location)

    if path.suffix.lower() != ".twd":
        raise ValueError("Only TWD templates are supported")

    imported = import_twd_file(path)

    rendered = HtmlMergeRenderer().render(
        imported.document,
        context,
        strict=False,
    )

    return TwdPreview(
        html=rendered.content,
        assets=imported.imported_assets,
        warnings=imported.warnings,
        unresolved_fields=rendered.unresolved_fields,
        unsupported_features=imported.unsupported_features,
    )
