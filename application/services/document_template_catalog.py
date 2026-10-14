from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping

from domain.documents import DocumentTemplate, target_from_mapping


class DocumentTemplateFormat(str, Enum):
    WORD_LEGACY = "doc"
    LIBREOFFICE = "odt"
    TEAMWORD = "twd"

    @property
    def suffix(self) -> str:
        return f".{self.value}"


@dataclass(frozen=True)
class DocumentTemplateFile:
    name: str
    path: Path
    format: DocumentTemplateFormat
    size_bytes: int
    modified_at: datetime


TemplateMetadataLoader = Callable[[str], Mapping[str, object] | None]


def legacy_software_choice_format(choice: int) -> DocumentTemplateFormat:
    """Traduit le choix historique du publiposteur sans dépendre de wx."""

    mapping = {
        1: DocumentTemplateFormat.WORD_LEGACY,
        2: DocumentTemplateFormat.LIBREOFFICE,
        3: DocumentTemplateFormat.TEAMWORD,
        4: DocumentTemplateFormat.TEAMWORD,
    }
    try:
        return mapping[int(choice)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Logiciel de publipostage inconnu : {choice}") from exc


def discover_document_template_files(
    directory: str | Path,
    *,
    template_format: DocumentTemplateFormat | None = None,
) -> tuple[DocumentTemplateFile, ...]:
    """Inventorie les modèles présents sans ouvrir Word, Writer ou Teamword."""

    directory = Path(directory)
    if not directory.is_dir():
        return ()

    allowed = (
        {template_format.suffix}
        if template_format is not None
        else {item.suffix for item in DocumentTemplateFormat}
    )
    result: list[DocumentTemplateFile] = []

    for path in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        stat = path.stat()
        format_value = DocumentTemplateFormat(path.suffix.lower().lstrip("."))
        result.append(
            DocumentTemplateFile(
                name=path.name,
                path=path,
                format=format_value,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
            )
        )

    return tuple(result)


def discover_document_templates(
    directory: str | Path,
    *,
    template_format: DocumentTemplateFormat | None = None,
    metadata_loader: TemplateMetadataLoader | None = None,
) -> tuple[DocumentTemplate, ...]:
    """Retourne le catalogue métier prêt à être filtré par le workflow RH."""

    files = discover_document_template_files(
        directory,
        template_format=template_format,
    )
    return tuple(
        DocumentTemplate(
            name=item.name,
            location=str(item.path),
            target=target_from_mapping(
                metadata_loader(item.name) if metadata_loader is not None else None
            ),
        )
        for item in files
    )
