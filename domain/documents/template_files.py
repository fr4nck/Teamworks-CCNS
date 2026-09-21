from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile

from .keywords import KeywordContext, extract_template_keywords, known_keywords


@dataclass(frozen=True)
class TemplateFileAudit:
    path: Path
    keywords: tuple[str, ...]
    unknown_keywords: tuple[str, ...]
    restricted_keywords: tuple[str, ...]
    readable: bool
    error: str | None = None


_RESTRICTED_BY_FLOW = {
    "BRUTJOUR": "contract_record_only",
}


def _tokens_from_text(text: str) -> tuple[str, ...]:
    return extract_template_keywords(text)


def _tokens_from_twd(path: Path) -> tuple[str, ...]:
    return _tokens_from_text(path.read_text(encoding="utf-8", errors="ignore"))


def _tokens_from_odt(path: Path) -> tuple[str, ...]:
    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".xml"):
                continue
            try:
                parts.append(archive.read(name).decode("utf-8", errors="ignore"))
            except KeyError:
                continue
    return _tokens_from_text("\n".join(parts))


_DOC_ASCII_TOKEN_RE = re.compile(rb"\{([A-Za-z0-9_]+)\}")


def _tokens_from_doc(path: Path) -> tuple[str, ...]:
    """Extrait uniquement les balises visibles d'un ancien fichier Word binaire.

    Le format .doc peut stocker le texte en ANSI ou UTF-16LE. Pour l'audit des
    jetons, il suffit de scanner ces deux représentations sans interpréter le
    document ni lancer Microsoft Word.
    """

    data = path.read_bytes()
    tokens: list[str] = []
    seen: set[str] = set()

    for match in _DOC_ASCII_TOKEN_RE.finditer(data):
        token = match.group(1).decode("ascii").upper()
        # Les conteneurs OLE des anciens .doc contiennent régulièrement des
        # séquences binaires ressemblant à "{E}". Aucun mot-clé standard livré
        # n'est mono-caractère : on les écarte pour éviter ce faux positif.
        if len(token) < 2:
            continue
        if token not in seen:
            seen.add(token)
            tokens.append(token)

    # Certains .doc stockent la partie texte en Unicode little-endian.
    unicode_text = data.decode("utf-16le", errors="ignore")
    for token in extract_template_keywords(unicode_text):
        if token not in seen:
            seen.add(token)
            tokens.append(token)

    return tuple(tokens)


def extract_template_file_keywords(path: str | Path) -> tuple[str, ...]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".twd":
        return _tokens_from_twd(path)
    if suffix == ".odt":
        return _tokens_from_odt(path)
    if suffix == ".doc":
        return _tokens_from_doc(path)
    raise ValueError(f"Format de modèle non pris en charge : {suffix or '<sans extension>'}")


def audit_template_file(
    path: str | Path,
    *,
    context: KeywordContext = KeywordContext.CONTRACT,
    extra_keywords: tuple[str, ...] = (),
) -> TemplateFileAudit:
    path = Path(path)
    try:
        tokens = extract_template_file_keywords(path)
    except Exception as exc:
        return TemplateFileAudit(
            path=path,
            keywords=(),
            unknown_keywords=(),
            restricted_keywords=(),
            readable=False,
            error=str(exc),
        )

    known = known_keywords(context=context, extra_keywords=extra_keywords)
    unknown = tuple(token for token in tokens if token not in known)
    restricted = tuple(token for token in tokens if token in _RESTRICTED_BY_FLOW)
    return TemplateFileAudit(
        path=path,
        keywords=tokens,
        unknown_keywords=unknown,
        restricted_keywords=restricted,
        readable=True,
    )


def audit_template_directory(
    directory: str | Path,
    *,
    context: KeywordContext = KeywordContext.CONTRACT,
    extra_keywords: tuple[str, ...] = (),
) -> tuple[TemplateFileAudit, ...]:
    directory = Path(directory)
    files = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in {".twd", ".odt", ".doc"}
    )
    return tuple(
        audit_template_file(path, context=context, extra_keywords=extra_keywords)
        for path in files
    )
