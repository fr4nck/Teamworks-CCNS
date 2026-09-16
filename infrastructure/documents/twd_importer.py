from __future__ import annotations

import hashlib
import html
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from domain.documents import (
    Asset,
    DEFAULT_DOCUMENT_FIELD_REGISTRY,
    DocumentMetadata,
    DocumentModel,
    MergeFieldRegistry,
    sanitize_html,
)
from domain.documents.legacy import upgrade_legacy_placeholders

WX_RICHTEXT_NAMESPACE = "http://www.wxwidgets.org"
WX_RICHTEXT_VERSION = "1.0.0.0"

_PLACEHOLDER_RE = re.compile(r"\{[A-Z][A-Z0-9_]*\}")

_TEXT_STYLE_ATTRS = {
    "textcolor",
    "bgcolor",
    "fontsize",
    "fontface",
    "fontweight",
    "fontstyle",
    "fontunderlined",
}
_PARAGRAPH_ATTRS = _TEXT_STYLE_ATTRS | {
    "alignment",
    "leftindent",
    "leftsubindent",
    "rightindent",
    "parspacingbefore",
    "parspacingafter",
    "linespacing",
    "pagebreak",
}
_TEXT_ATTRS = _TEXT_STYLE_ATTRS | {"url"}
_IMAGE_ATTRS = {"imagetype"}


class LegacyTwdImportError(ValueError):
    """Raised when a source cannot be interpreted as a Teamword wxRichText document."""


@dataclass(frozen=True)
class LegacyImportResult:
    document: DocumentModel
    source: str
    source_hash: str
    warnings: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    imported_assets: tuple[Asset, ...]
    placeholders_recognized: tuple[str, ...]
    placeholders_unknown: tuple[str, ...]


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _tag_parts(tag: str) -> tuple[str, str]:
    if tag.startswith("{") and "}" in tag:
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def _local_name(tag: str) -> str:
    return _tag_parts(tag)[1]


def _css_number(value: str) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def _tenths_mm(value: str) -> str:
    return f"{_css_number(str(float(value) / 10.0))}mm"


def _font_weight(value: str) -> str | None:
    # Historical wx enum compatibility values found in Teamword files.
    if value == "90":
        return "400"
    if value == "91":
        return "300"
    if value == "92":
        return "700"
    try:
        numeric = int(value)
    except ValueError:
        return None
    if 1 <= numeric <= 1000:
        return str(numeric)
    return None


def _font_style(value: str) -> str | None:
    if value == "90":
        return "normal"
    if value in {"93", "94"}:
        return "italic"
    return None


def _alignment(value: str) -> str | None:
    return {
        "1": "left",
        "2": "center",
        "3": "right",
        "4": "justify",
    }.get(value)


def _line_height(value: str) -> str | None:
    return {"10": "1", "15": "1.5", "20": "2"}.get(value)


def _record_unknown_attrs(
    attrs: dict[str, str],
    allowed: set[str],
    *,
    context: str,
    warnings: list[str],
    unsupported: list[str],
) -> None:
    for name in attrs:
        if name in allowed:
            continue
        feature = f"{context}-attribute:{name}"
        unsupported.append(feature)
        warnings.append(f"Attribut wxRichText non pris en charge ({context}): {name}")


def _style_from_attrs(
    attrs: dict[str, str],
    *,
    paragraph: bool,
    warnings: list[str],
    unsupported: list[str],
) -> dict[str, str]:
    style: dict[str, str] = {}

    if "textcolor" in attrs:
        style["color"] = attrs["textcolor"]
    if "bgcolor" in attrs:
        style["background-color"] = attrs["bgcolor"]
    if "fontsize" in attrs:
        try:
            style["font-size"] = f"{_css_number(attrs['fontsize'])}pt"
        except ValueError:
            warnings.append(f"Taille de police wx invalide ignorée: {attrs['fontsize']!r}")
    if "fontface" in attrs and attrs["fontface"].strip():
        style["font-family"] = attrs["fontface"].strip()
    if "fontweight" in attrs:
        weight = _font_weight(attrs["fontweight"])
        if weight is None:
            warnings.append(f"Poids de police wx non reconnu: {attrs['fontweight']!r}")
            unsupported.append(f"fontweight:{attrs['fontweight']}")
        else:
            style["font-weight"] = weight
    if "fontstyle" in attrs:
        font_style = _font_style(attrs["fontstyle"])
        if font_style is None:
            warnings.append(f"Style de police wx non reconnu: {attrs['fontstyle']!r}")
            unsupported.append(f"fontstyle:{attrs['fontstyle']}")
        else:
            style["font-style"] = font_style
    if attrs.get("fontunderlined") not in (None, "0"):
        style["text-decoration"] = "underline"

    if paragraph:
        if "alignment" in attrs:
            alignment = _alignment(attrs["alignment"])
            if alignment is None:
                warnings.append(f"Alignement wx non reconnu: {attrs['alignment']!r}")
                unsupported.append(f"alignment:{attrs['alignment']}")
            else:
                style["text-align"] = alignment
        for attribute, css_name in (
            ("leftindent", "margin-left"),
            ("rightindent", "margin-right"),
            ("parspacingbefore", "margin-top"),
            ("parspacingafter", "margin-bottom"),
        ):
            if attribute in attrs:
                try:
                    style[css_name] = _tenths_mm(attrs[attribute])
                except ValueError:
                    warnings.append(f"Mesure wx invalide {attribute}={attrs[attribute]!r}")
                    unsupported.append(f"{attribute}:{attrs[attribute]}")
        if "leftsubindent" in attrs and attrs["leftsubindent"] not in {"", "0"}:
            # CSS hanging indent is not equivalent in all renderers. Preserve the
            # information as a warning rather than pretending to be lossless.
            warnings.append(
                "leftsubindent wx non nul conservé avec perte potentielle de mise en page "
                f"({attrs['leftsubindent']})"
            )
            unsupported.append("leftsubindent")
        if "linespacing" in attrs:
            line_height = _line_height(attrs["linespacing"])
            if line_height is None:
                warnings.append(f"Interligne wx non reconnu: {attrs['linespacing']!r}")
                unsupported.append(f"linespacing:{attrs['linespacing']}")
            else:
                style["line-height"] = line_height
        if attrs.get("pagebreak") not in (None, "0"):
            style["page-break-before"] = "always"

    return style


def _style_attr(style: dict[str, str]) -> str:
    if not style:
        return ""
    serialized = "; ".join(f"{name}: {value}" for name, value in style.items())
    return f' style="{html.escape(serialized, quote=True)}"'


def _render_text_value(value: str) -> str:
    # wxRichText uses character 29 as an in-paragraph line-break marker; XML
    # serializes it as <symbol>29</symbol>. Literal tabs are converted to NBSP
    # runs because normal HTML whitespace collapsing would otherwise lose them.
    escaped = html.escape(value, quote=False)
    escaped = escaped.replace("\t", "\u00a0" * 4)
    escaped = escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return escaped


def _detect_asset_type(content: bytes) -> tuple[str, str]:
    if content.startswith(b"BM"):
        return "image/bmp", ".bmp"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif", ".gif"
    return "application/octet-stream", ".bin"


def _extract_placeholders(root: ET.Element, registry: MergeFieldRegistry) -> tuple[tuple[str, ...], tuple[str, ...]]:
    found: list[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "text":
            continue
        for token in _PLACEHOLDER_RE.findall(element.text or ""):
            if token not in found:
                found.append(token)
    recognized = tuple(token for token in found if registry.get_by_legacy_token(token) is not None)
    unknown = tuple(token for token in found if registry.get_by_legacy_token(token) is None)
    return recognized, unknown


def import_twd_bytes(
    source_bytes: bytes,
    *,
    source: str,
    document_type: str = "legacy_teamword",
    registry: MergeFieldRegistry = DEFAULT_DOCUMENT_FIELD_REGISTRY,
) -> LegacyImportResult:
    """Import a Teamword TWD without mutating the source or importing wxPython.

    The implementation targets the observed wxWidgets RichText XML format. Any
    structure not explicitly understood is reported and its textual content is
    retained whenever possible instead of being silently discarded.
    """

    source_hash = hashlib.sha256(source_bytes).hexdigest()
    upper_source = source_bytes.upper()
    if b"<!DOCTYPE" in upper_source or b"<!ENTITY" in upper_source:
        raise LegacyTwdImportError(f"DTD/entités XML interdits dans un TWD: {source}")
    try:
        root = ET.fromstring(source_bytes)
    except (ET.ParseError, ValueError) as exc:
        raise LegacyTwdImportError(f"TWD XML invalide: {source}") from exc

    namespace, root_name = _tag_parts(root.tag)
    if root_name != "richtext":
        raise LegacyTwdImportError(f"Racine TWD inattendue {root_name!r}: {source}")
    if namespace != WX_RICHTEXT_NAMESPACE:
        raise LegacyTwdImportError(
            f"Namespace TWD inattendu {namespace!r}; attendu {WX_RICHTEXT_NAMESPACE!r}: {source}"
        )

    warnings: list[str] = []
    unsupported: list[str] = []
    version = root.attrib.get("version", "")
    if version != WX_RICHTEXT_VERSION:
        warnings.append(f"Version wxRichText non qualifiée: {version or '<absente>'}")
        unsupported.append(f"richtext-version:{version or 'absent'}")

    recognized, unknown = _extract_placeholders(root, registry)
    if unknown:
        warnings.append(
            "Variables historiques non mappées sémantiquement mais conservées: " + ", ".join(unknown)
        )

    layout_nodes = [child for child in root if _local_name(child.tag) == "paragraphlayout"]
    if not layout_nodes:
        raise LegacyTwdImportError(f"Aucun paragraphlayout wxRichText dans {source}")
    if len(layout_nodes) > 1:
        warnings.append(f"{len(layout_nodes)} paragraphlayout détectés; import séquentiel")

    for child in root:
        local = _local_name(child.tag)
        if local not in {"paragraphlayout", "richtext-version"}:
            unsupported.append(f"root-element:{local}")
            warnings.append(f"Élément racine wxRichText non pris en charge: {local}")

    assets: list[Asset] = []
    html_parts: list[str] = []
    symbol_29_count = 0

    for layout in layout_nodes:
        layout_attrs = dict(layout.attrib)
        _record_unknown_attrs(
            layout_attrs,
            _PARAGRAPH_ATTRS,
            context="paragraphlayout",
            warnings=warnings,
            unsupported=unsupported,
        )
        for child in layout:
            local = _local_name(child.tag)
            if local != "paragraph":
                unsupported.append(f"layout-element:{local}")
                warnings.append(f"Élément paragraphlayout non pris en charge: {local}")
                fallback = "".join(child.itertext())
                if fallback:
                    html_parts.append(f"<p>{html.escape(fallback, quote=False)}</p>")
                continue

            _record_unknown_attrs(
                dict(child.attrib),
                _PARAGRAPH_ATTRS,
                context="paragraph",
                warnings=warnings,
                unsupported=unsupported,
            )
            paragraph_attrs = dict(layout_attrs)
            paragraph_attrs.update(child.attrib)
            paragraph_style = _style_from_attrs(
                paragraph_attrs,
                paragraph=True,
                warnings=warnings,
                unsupported=unsupported,
            )
            paragraph_chunks: list[str] = []

            for inline in child:
                inline_name = _local_name(inline.tag)
                if inline_name == "text":
                    _record_unknown_attrs(
                        dict(inline.attrib),
                        _TEXT_ATTRS,
                        context="text",
                        warnings=warnings,
                        unsupported=unsupported,
                    )
                    text_attrs = dict(paragraph_attrs)
                    text_attrs.update(inline.attrib)
                    text_style = _style_from_attrs(
                        text_attrs,
                        paragraph=False,
                        warnings=warnings,
                        unsupported=unsupported,
                    )
                    value = _render_text_value(inline.text or "")
                    if text_style:
                        value = f"<span{_style_attr(text_style)}>{value}</span>"
                    url = inline.attrib.get("url", "").strip()
                    if url:
                        value = f'<a href="{html.escape(url, quote=True)}">{value}</a>'
                    paragraph_chunks.append(value)
                    continue

                if inline_name == "symbol":
                    value = (inline.text or "").strip()
                    if value == "29":
                        symbol_29_count += 1
                        paragraph_chunks.append("<br>")
                    else:
                        unsupported.append(f"symbol:{value or 'empty'}")
                        warnings.append(f"Symbole wxRichText non pris en charge: {value or '<vide>'}")
                        paragraph_chunks.append(html.escape(f"[symbol:{value}]", quote=False))
                    continue

                if inline_name == "image":
                    _record_unknown_attrs(
                        dict(inline.attrib),
                        _IMAGE_ATTRS,
                        context="image",
                        warnings=warnings,
                        unsupported=unsupported,
                    )
                    data_node = next((item for item in inline if _local_name(item.tag) == "data"), None)
                    raw_hex = "" if data_node is None else "".join((data_node.text or "").split())
                    try:
                        content = bytes.fromhex(raw_hex)
                    except ValueError:
                        content = b""
                    if not content:
                        unsupported.append("image-data")
                        warnings.append("Image wxRichText sans données hexadécimales valides")
                        paragraph_chunks.append("[image non importée]")
                        continue
                    mime_type, extension = _detect_asset_type(content)
                    image_index = len(assets) + 1
                    asset_sha = hashlib.sha256(content).hexdigest()
                    asset_id = str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"teamworks-twd-asset:{source_hash}:{image_index}:{asset_sha}",
                        )
                    )
                    asset = Asset.from_bytes(
                        content=content,
                        mime_type=mime_type,
                        name=f"{Path(source).stem}-image-{image_index}{extension}",
                        asset_id=asset_id,
                        metadata={
                            "legacy_format": "wx-richtext-xml",
                            "legacy_imagetype": inline.attrib.get("imagetype", ""),
                            "legacy_sha256": asset_sha,
                        },
                    )
                    assets.append(asset)
                    if mime_type == "application/octet-stream":
                        unsupported.append("image-format")
                        warnings.append(
                            f"Format d'image embarquée non identifié pour {asset.name}; octets conservés"
                        )
                    paragraph_chunks.append(f'<img src="{asset.uri}" alt="{html.escape(asset.name, quote=True)}">')
                    continue

                unsupported.append(f"paragraph-element:{inline_name}")
                warnings.append(f"Élément wxRichText non pris en charge dans un paragraphe: {inline_name}")
                fallback = "".join(inline.itertext())
                if fallback:
                    paragraph_chunks.append(html.escape(fallback, quote=False))

            html_parts.append(f"<p{_style_attr(paragraph_style)}>{''.join(paragraph_chunks)}</p>")

    upgraded_html = upgrade_legacy_placeholders("".join(html_parts), registry)
    canonical_html = sanitize_html(upgraded_html)

    metadata_attributes = {
        "legacy_format": "wx-richtext-xml",
        "legacy_namespace": namespace,
        "legacy_version": version,
        "legacy_source": source,
        "legacy_source_sha256": source_hash,
    }
    if symbol_29_count:
        # Informational provenance, not a loss: wx sample code itself uses char 29
        # as an in-paragraph line break and the XML handler serializes it as a symbol.
        metadata_attributes["legacy_symbol_29_line_breaks"] = symbol_29_count

    metadata = DocumentMetadata(
        title=Path(source).stem,
        owner_domain="rh",
        language="fr-FR",
        attributes=metadata_attributes,
    )
    document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"teamworks-twd-document:{source_hash}"))
    document = DocumentModel.create(
        document_type=document_type,
        html=canonical_html,
        metadata=metadata,
        assets=tuple(assets),
        document_id=document_id,
    )

    return LegacyImportResult(
        document=document,
        source=source,
        source_hash=source_hash,
        warnings=_unique(warnings),
        unsupported_features=_unique(unsupported),
        imported_assets=tuple(assets),
        placeholders_recognized=recognized,
        placeholders_unknown=unknown,
    )


def import_twd_file(
    path: str | Path,
    *,
    document_type: str = "legacy_teamword",
    registry: MergeFieldRegistry = DEFAULT_DOCUMENT_FIELD_REGISTRY,
) -> LegacyImportResult:
    source_path = Path(path)
    return import_twd_bytes(
        source_path.read_bytes(),
        source=source_path.as_posix(),
        document_type=document_type,
        registry=registry,
    )
