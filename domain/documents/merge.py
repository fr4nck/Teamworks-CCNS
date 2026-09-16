from __future__ import annotations

import html
from dataclasses import dataclass
from html.parser import HTMLParser

from .fields import DEFAULT_DOCUMENT_FIELD_REGISTRY, MergeFieldRegistry
from .html_format import sanitize_html
from .merge_context import MergeContext
from .model import DocumentModel


class MergeError(ValueError):
    pass


class UnknownMergeFieldError(MergeError):
    def __init__(self, fields: tuple[str, ...]) -> None:
        self.fields = fields
        super().__init__("Unknown or missing merge fields: " + ", ".join(fields))


@dataclass(frozen=True)
class RenderResult:
    content: str
    media_type: str = "text/html; charset=utf-8"
    used_fields: tuple[str, ...] = ()
    unresolved_fields: tuple[str, ...] = ()


class _SemanticFieldRenderer(HTMLParser):
    def __init__(self, context: MergeContext, registry: MergeFieldRegistry) -> None:
        super().__init__(convert_charrefs=True)
        self.context = context
        self.registry = registry
        self.parts: list[str] = []
        self.used: list[str] = []
        self.unresolved: list[str] = []
        self._field_suppression_depth = 0

    def _context_value(self, canonical_key: str, aliases: tuple[str, ...]) -> tuple[bool, object]:
        if canonical_key in self.context.values:
            return True, self.context.values[canonical_key]
        for alias in aliases:
            normalized = alias.strip().upper()
            if normalized in self.context.values:
                return True, self.context.values[normalized]
        return False, ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._field_suppression_depth:
            self._field_suppression_depth += 1
            return
        if tag == "span":
            attr_map = {name.lower(): value for name, value in attrs if value is not None}
            raw_key = attr_map.get("data-pmsl-field")
            if raw_key:
                merge_field = self.registry.get(raw_key)
                canonical = merge_field.key if merge_field else raw_key.strip().upper()
                if merge_field is None:
                    found, value = False, ""
                else:
                    found, value = self._context_value(canonical, merge_field.aliases)
                if found and value not in (None, ""):
                    self.parts.append(html.escape(str(value), quote=False))
                    if canonical not in self.used:
                        self.used.append(canonical)
                else:
                    self.parts.append("{%s}" % canonical)
                    if canonical not in self.unresolved:
                        self.unresolved.append(canonical)
                self._field_suppression_depth = 1
                return
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in attrs if value is not None)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._field_suppression_depth:
            return
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in attrs if value is not None)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        if self._field_suppression_depth:
            self._field_suppression_depth -= 1
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._field_suppression_depth:
            self.parts.append(html.escape(data, quote=False))


class HtmlMergeRenderer:
    """Pure-Python renderer for canonical semantic HTML fields."""

    def __init__(self, registry: MergeFieldRegistry = DEFAULT_DOCUMENT_FIELD_REGISTRY) -> None:
        self.registry = registry

    def render(self, document: DocumentModel, context: MergeContext, *, strict: bool = False) -> RenderResult:
        canonical_html = sanitize_html(document.html)
        parser = _SemanticFieldRenderer(context, self.registry)
        parser.feed(canonical_html)
        parser.close()
        unresolved = tuple(parser.unresolved)
        if strict and unresolved:
            raise UnknownMergeFieldError(unresolved)
        return RenderResult(content="".join(parser.parts), used_fields=tuple(parser.used), unresolved_fields=unresolved)
