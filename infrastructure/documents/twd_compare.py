from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable
from xml.etree import ElementTree as ET

WX_RICHTEXT_NAMESPACE = "http://www.wxwidgets.org"
_PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_]*\}")
_XML_DECL_RE = re.compile(br"^\s*(<\?xml[^?]*\?>)", re.IGNORECASE)

_KNOWN_TAGS = {
    "richtext",
    "richtext-version",
    "paragraphlayout",
    "paragraph",
    "text",
    "image",
    "data",
    "symbol",
    "stylesheet",
    "characterstyle",
    "paragraphstyle",
    "liststyle",
    "boxstyle",
    "table",
    "cell",
}

_STYLE_ATTRS = {
    "textcolor",
    "bgcolor",
    "fontsize",
    "fontface",
    "fontweight",
    "fontstyle",
    "fontunderlined",
    "alignment",
    "leftindent",
    "leftsubindent",
    "rightindent",
    "parspacingbefore",
    "parspacingafter",
    "linespacing",
    "pagebreak",
    "url",
}


class TwdInspectionError(ValueError):
    """Raised when a TWD cannot be structurally inspected."""


@dataclass(frozen=True)
class TwdInventory:
    source: str
    source_hash: str
    size: int
    file_date: str | None
    xml_declaration: str
    namespace: str
    richtext_version: str
    tags: tuple[str, ...]
    attributes: tuple[str, ...]
    paragraph_count: int
    text_run_count: int
    image_count: int
    image_types: tuple[str, ...]
    asset_hashes: tuple[str, ...]
    symbol_count: int
    symbols: tuple[str, ...]
    placeholders: tuple[str, ...]
    styles: tuple[str, ...]
    alignments: tuple[str, ...]
    indents: tuple[str, ...]
    colors: tuple[str, ...]
    fonts: tuple[str, ...]
    font_sizes: tuple[str, ...]
    links: tuple[str, ...]
    table_count: int
    page_break_count: int
    unknown_structures: tuple[str, ...]
    logical_sequence: tuple[str, ...]
    text_content: tuple[str, ...]


@dataclass(frozen=True)
class TwdStructuralDiff:
    source_a: str
    source_b: str
    same_format: bool
    structural_changes: tuple[str, ...]
    content_changes: tuple[str, ...]
    style_changes: tuple[str, ...]
    asset_changes: tuple[str, ...]
    placeholder_changes: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def is_identical(self) -> bool:
        return not any(
            (
                self.structural_changes,
                self.content_changes,
                self.style_changes,
                self.asset_changes,
                self.placeholder_changes,
            )
        )

    @property
    def potentially_incompatible(self) -> bool:
        return (not self.same_format) or bool(
            [item for item in self.structural_changes if item.startswith("unknown-")]
        )


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _tag_parts(tag: str) -> tuple[str, str]:
    if tag.startswith("{") and "}" in tag:
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def _local_name(tag: str) -> str:
    return _tag_parts(tag)[1]


def _image_type(raw: bytes) -> str:
    if raw.startswith(b"BM"):
        return "image/bmp"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    return "application/octet-stream"


def _serialize_style(element: ET.Element) -> str:
    parts = [f"{name}={element.attrib[name]}" for name in sorted(element.attrib) if name in _STYLE_ATTRS]
    return f"{_local_name(element.tag)}:" + ";".join(parts)


def inspect_twd_bytes(
    source_bytes: bytes,
    *,
    source: str,
    file_date: str | None = None,
) -> TwdInventory:
    """Return a normalized, UI-free inventory of a wxRichText TWD document."""

    source_hash = hashlib.sha256(source_bytes).hexdigest()
    upper_source = source_bytes.upper()
    if b"<!DOCTYPE" in upper_source or b"<!ENTITY" in upper_source:
        raise TwdInspectionError(f"DTD/entités XML interdits dans un TWD: {source}")
    try:
        root = ET.fromstring(source_bytes)
    except (ET.ParseError, ValueError) as exc:
        raise TwdInspectionError(f"TWD XML invalide: {source}") from exc

    namespace, root_name = _tag_parts(root.tag)
    if root_name != "richtext":
        raise TwdInspectionError(f"Racine TWD inattendue {root_name!r}: {source}")

    xml_decl_match = _XML_DECL_RE.search(source_bytes)
    xml_declaration = (
        xml_decl_match.group(1).decode("ascii", errors="replace") if xml_decl_match else ""
    )

    tags: list[str] = []
    attributes: list[str] = []
    placeholders: list[str] = []
    styles: list[str] = []
    alignments: list[str] = []
    indents: list[str] = []
    colors: list[str] = []
    fonts: list[str] = []
    font_sizes: list[str] = []
    links: list[str] = []
    image_types: list[str] = []
    asset_hashes: list[str] = []
    symbols: list[str] = []
    unknown_structures: list[str] = []
    logical_sequence: list[str] = []
    text_content: list[str] = []
    paragraph_count = 0
    text_run_count = 0
    image_count = 0
    table_count = 0
    page_break_count = 0

    for element in root.iter():
        local = _local_name(element.tag)
        tags.append(local)
        logical_sequence.append(local)
        if local not in _KNOWN_TAGS:
            unknown_structures.append(f"element:{local}")
        for name in element.attrib:
            attributes.append(f"{local}.{name}")
        if any(name in _STYLE_ATTRS for name in element.attrib):
            styles.append(_serialize_style(element))
        if "alignment" in element.attrib:
            alignments.append(element.attrib["alignment"])
        for name in ("leftindent", "leftsubindent", "rightindent"):
            if name in element.attrib:
                indents.append(f"{name}={element.attrib[name]}")
        for name in ("textcolor", "bgcolor"):
            if name in element.attrib:
                colors.append(element.attrib[name])
        if "fontface" in element.attrib:
            fonts.append(element.attrib["fontface"])
        if "fontsize" in element.attrib:
            font_sizes.append(element.attrib["fontsize"])
        if "url" in element.attrib:
            links.append(element.attrib["url"])
        if element.attrib.get("pagebreak") not in (None, "", "0"):
            page_break_count += 1

        if local == "paragraph":
            paragraph_count += 1
        elif local == "text":
            text_run_count += 1
            value = element.text or ""
            text_content.append(value)
            placeholders.extend(_PLACEHOLDER_RE.findall(value))
        elif local == "symbol":
            symbols.append((element.text or "").strip())
        elif local == "image":
            image_count += 1
            data_node = next((child for child in element if _local_name(child.tag) == "data"), None)
            raw_hex = "" if data_node is None else "".join((data_node.text or "").split())
            try:
                raw = bytes.fromhex(raw_hex)
            except ValueError:
                raw = b""
            if raw:
                image_types.append(_image_type(raw))
                asset_hashes.append(hashlib.sha256(raw).hexdigest())
            else:
                image_types.append("invalid")
                asset_hashes.append("invalid")
        elif local == "table":
            table_count += 1

    return TwdInventory(
        source=source,
        source_hash=source_hash,
        size=len(source_bytes),
        file_date=file_date,
        xml_declaration=xml_declaration,
        namespace=namespace,
        richtext_version=root.attrib.get("version", ""),
        tags=_unique(tags),
        attributes=_unique(attributes),
        paragraph_count=paragraph_count,
        text_run_count=text_run_count,
        image_count=image_count,
        image_types=_unique(image_types),
        asset_hashes=tuple(asset_hashes),
        symbol_count=len(symbols),
        symbols=tuple(symbols),
        placeholders=_unique(placeholders),
        styles=_unique(styles),
        alignments=_unique(alignments),
        indents=_unique(indents),
        colors=_unique(colors),
        fonts=_unique(fonts),
        font_sizes=_unique(font_sizes),
        links=_unique(links),
        table_count=table_count,
        page_break_count=page_break_count,
        unknown_structures=_unique(unknown_structures),
        logical_sequence=tuple(logical_sequence),
        text_content=tuple(text_content),
    )


def _set_change(label: str, a: tuple[str, ...], b: tuple[str, ...]) -> str | None:
    if a == b:
        return None
    return f"{label}: {a!r} -> {b!r}"


def compare_twd_bytes(
    source_a: bytes,
    source_b: bytes,
    *,
    name_a: str,
    name_b: str,
) -> TwdStructuralDiff:
    """Compare TWDs semantically instead of diffing raw XML text."""

    a = inspect_twd_bytes(source_a, source=name_a)
    b = inspect_twd_bytes(source_b, source=name_b)
    structural: list[str] = []
    content: list[str] = []
    style: list[str] = []
    assets: list[str] = []
    placeholders: list[str] = []
    warnings: list[str] = []

    same_format = (a.namespace, a.richtext_version) == (b.namespace, b.richtext_version)
    if not same_format:
        structural.append(
            "format: "
            f"{(a.namespace, a.richtext_version)!r} -> {(b.namespace, b.richtext_version)!r}"
        )
        warnings.append("Différence potentiellement incompatible de namespace/version wxRichText")

    for label, left, right in (
        ("tags", a.tags, b.tags),
        ("attributes", a.attributes, b.attributes),
        ("unknown-structures", a.unknown_structures, b.unknown_structures),
        ("logical-order", a.logical_sequence, b.logical_sequence),
    ):
        change = _set_change(label, left, right)
        if change:
            structural.append(change)
    for label, left, right in (
        ("paragraph-count", a.paragraph_count, b.paragraph_count),
        ("text-run-count", a.text_run_count, b.text_run_count),
        ("symbol-count", a.symbol_count, b.symbol_count),
        ("symbols", a.symbols, b.symbols),
        ("table-count", a.table_count, b.table_count),
        ("page-break-count", a.page_break_count, b.page_break_count),
    ):
        if left != right:
            structural.append(f"{label}: {left!r} -> {right!r}")

    if a.text_content != b.text_content:
        content.append("text-content changed")

    for label, left, right in (
        ("styles", a.styles, b.styles),
        ("alignments", a.alignments, b.alignments),
        ("indents", a.indents, b.indents),
        ("colors", a.colors, b.colors),
        ("fonts", a.fonts, b.fonts),
        ("font-sizes", a.font_sizes, b.font_sizes),
        ("links", a.links, b.links),
    ):
        change = _set_change(label, left, right)
        if change:
            style.append(change)

    if a.image_count != b.image_count:
        assets.append(f"image-count: {a.image_count} -> {b.image_count}")
    if a.image_types != b.image_types:
        assets.append(f"image-types: {a.image_types!r} -> {b.image_types!r}")
    if a.asset_hashes != b.asset_hashes:
        assets.append("embedded asset bytes changed")

    if a.placeholders != b.placeholders:
        placeholders.append(f"placeholders: {a.placeholders!r} -> {b.placeholders!r}")

    if a.source_hash != b.source_hash and not any((structural, content, style, assets, placeholders)):
        warnings.append("Octets XML différents mais représentation structurelle normalisée identique (différence cosmétique)")

    return TwdStructuralDiff(
        source_a=name_a,
        source_b=name_b,
        same_format=same_format,
        structural_changes=tuple(structural),
        content_changes=tuple(content),
        style_changes=tuple(style),
        asset_changes=tuple(assets),
        placeholder_changes=tuple(placeholders),
        warnings=tuple(warnings),
    )
