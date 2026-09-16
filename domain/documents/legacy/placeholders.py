from __future__ import annotations

import html
import re
from html.parser import HTMLParser

from ..fields import DEFAULT_DOCUMENT_FIELD_REGISTRY, MergeFieldRegistry

_TOKEN_RE = re.compile(r"\{[A-Z][A-Z0-9_]*\}")


class _LegacyPlaceholderUpgrader(HTMLParser):
    def __init__(self, registry: MergeFieldRegistry) -> None:
        super().__init__(convert_charrefs=True)
        self.registry = registry
        self.parts: list[str] = []
        self.semantic_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "span" and any(name.lower() == "data-pmsl-field" and value for name, value in attrs):
            self.semantic_depth += 1
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in attrs if value is not None)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in attrs if value is not None)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")
        if tag == "span" and self.semantic_depth:
            self.semantic_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.semantic_depth:
            self.parts.append(html.escape(data, quote=False))
            return
        position = 0
        for match in _TOKEN_RE.finditer(data):
            self.parts.append(html.escape(data[position:match.start()], quote=False))
            token = match.group(0)
            merge_field = self.registry.get_by_legacy_token(token)
            if merge_field is None:
                self.parts.append(html.escape(token, quote=False))
            else:
                self.parts.append('<span data-pmsl-field="%s">%s</span>' % (merge_field.key, html.escape(token, quote=False)))
            position = match.end()
        self.parts.append(html.escape(data[position:], quote=False))


def upgrade_legacy_placeholders(raw_html: str, registry: MergeFieldRegistry = DEFAULT_DOCUMENT_FIELD_REGISTRY) -> str:
    """Convert known historical {KEY} text tokens into canonical semantic fields."""
    parser = _LegacyPlaceholderUpgrader(registry)
    parser.feed(raw_html or "")
    parser.close()
    return "".join(parser.parts)
