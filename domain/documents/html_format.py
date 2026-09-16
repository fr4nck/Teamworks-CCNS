from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

_ALLOWED_TAGS = {"p", "br", "div", "span", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "a", "img", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "hr"}
_BLOCKED_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed"}
_VOID_TAGS = {"br", "img", "hr"}
_ALLOWED_STYLE_PROPERTIES = {"text-align", "color", "background-color", "font-size", "font-family", "font-weight", "font-style", "text-decoration", "margin-left", "margin-right", "page-break-before", "page-break-after", "break-before", "break-after", "width", "height", "vertical-align"}
_SAFE_LINK_SCHEMES = {"http", "https", "mailto", "tel"}
_FIELD_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_ASSET_URI_RE = re.compile(r"^asset://[0-9a-fA-F-]{36}$")


def _clean_style(raw: str) -> str:
    declarations: list[str] = []
    for declaration in raw.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        name, value = name.strip().lower(), value.strip()
        lowered = value.lower()
        if name not in _ALLOWED_STYLE_PROPERTIES:
            continue
        if any(marker in lowered for marker in ("url(", "expression(", "javascript:", "data:")):
            continue
        if value:
            declarations.append(f"{name}: {value}")
    return "; ".join(declarations)


def _safe_href(raw: str) -> str | None:
    value = raw.strip()
    if not value:
        return None
    if value.startswith("#"):
        return value
    return value if urlparse(value).scheme.lower() in _SAFE_LINK_SCHEMES else None


def _safe_img_src(raw: str) -> str | None:
    value = raw.strip()
    return value if _ASSET_URI_RE.match(value) else None


def _allowed_attribute(tag: str, name: str, value: str) -> tuple[str, str] | None:
    lname = name.lower()
    if lname.startswith("on"):
        return None
    if lname == "style":
        cleaned = _clean_style(value)
        return ("style", cleaned) if cleaned else None
    if tag == "span" and lname == "data-pmsl-field":
        normalized = value.strip().upper()
        return (lname, normalized) if _FIELD_KEY_RE.match(normalized) else None
    if tag == "a" and lname == "href":
        safe = _safe_href(value)
        return (lname, safe) if safe else None
    if tag == "a" and lname == "title":
        return lname, value
    if tag == "img" and lname == "src":
        safe = _safe_img_src(value)
        return (lname, safe) if safe else None
    if tag == "img" and lname in {"alt", "title", "width", "height"}:
        return lname, value
    if tag in {"td", "th"} and lname in {"colspan", "rowspan"}:
        return lname, value
    if lname == "align" and tag in {"p", "div", "td", "th"}:
        return lname, value
    return None


class _Sanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.blocked_depth = 0
        self.open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.blocked_depth:
            if tag in _BLOCKED_CONTENT_TAGS:
                self.blocked_depth += 1
            return
        if tag in _BLOCKED_CONTENT_TAGS:
            self.blocked_depth = 1
            return
        if tag not in _ALLOWED_TAGS:
            return
        cleaned_attrs = []
        for name, value in attrs:
            if value is None:
                continue
            cleaned = _allowed_attribute(tag, name, value)
            if cleaned is not None:
                cleaned_attrs.append(cleaned)
        attr_text = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in cleaned_attrs)
        self.parts.append(f"<{tag}{attr_text}>")
        if tag not in _VOID_TAGS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        tag = tag.lower()
        if tag not in _VOID_TAGS and self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()
            self.parts.append(f"</{tag}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.blocked_depth:
            if tag in _BLOCKED_CONTENT_TAGS:
                self.blocked_depth -= 1
            return
        if tag not in _ALLOWED_TAGS or tag in _VOID_TAGS:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.parts.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        if not self.blocked_depth:
            self.parts.append(html.escape(data, quote=False))

    def handle_comment(self, data: str) -> None:
        return

    def close_all(self) -> None:
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")


def sanitize_html(raw_html: str) -> str:
    parser = _Sanitizer()
    parser.feed(raw_html or "")
    parser.close()
    parser.close_all()
    return "".join(parser.parts)
