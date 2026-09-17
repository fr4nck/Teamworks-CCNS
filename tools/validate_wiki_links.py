#!/usr/bin/env python3
"""Contrôle léger des liens internes et ancres explicites du wiki.

Les URL externes sont volontairement ignorées afin de ne pas rendre la CI fragile.
"""
from __future__ import annotations

import re
import urllib.parse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "docs" / "wiki"


def wiki_slug(stem: str) -> str:
    return stem.replace(" ", "-")


def collect_pages() -> tuple[dict[str, Path], dict[str, str], list[str]]:
    pages: dict[str, Path] = {}
    aliases: dict[str, str] = {}
    errors: list[str] = []
    for path in sorted(WIKI.glob("*.md")):
        pages[path.stem] = path
        aliases[path.stem] = path.stem
        aliases[wiki_slug(path.stem)] = path.stem
        text = path.read_text(encoding="utf-8")
        anchors = re.findall(r'<a\s+id="([^"]+)"\s*></a>', text)
        for anchor, count in Counter(anchors).items():
            if count > 1:
                errors.append(f"ancre dupliquée dans {path.name}: #{anchor} ({count} fois)")
    return pages, aliases, errors


def anchors_for(path: Path) -> set[str]:
    return set(re.findall(r'<a\s+id="([^"]+)"\s*></a>', path.read_text(encoding="utf-8")))


def resolve_target(raw: str, aliases: dict[str, str]) -> tuple[str | None, str | None]:
    raw = urllib.parse.unquote(raw.strip())
    if raw.startswith(("http://", "https://", "mailto:")):
        return None, None
    page, sep, anchor = raw.partition("#")
    if page.endswith(".md"):
        page = page[:-3]
    page = page.strip("./")
    if not page:
        return "", anchor if sep else ""
    if page in aliases:
        return aliases[page], anchor if sep else ""
    return page, anchor if sep else ""


def main() -> int:
    pages, aliases, errors = collect_pages()
    anchor_cache = {stem: anchors_for(path) for stem, path in pages.items()}
    checked = 0

    for stem, path in pages.items():
        text = path.read_text(encoding="utf-8")

        for inner in re.findall(r'\[\[([^\]]+)\]\]', text):
            target = inner.split("|", 1)[1] if "|" in inner else inner
            page_raw, sep, anchor = target.partition("#")
            page_raw = page_raw.strip()
            page = aliases.get(page_raw, aliases.get(wiki_slug(page_raw), page_raw))
            checked += 1
            if page not in pages:
                errors.append(f"page inexistante dans {path.name}: [[{inner}]]")
            elif sep and anchor and anchor not in anchor_cache[page]:
                errors.append(f"ancre absente dans {path.name}: [[{inner}]]")

        for raw in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
            raw = raw.split(" ", 1)[0]
            page, anchor = resolve_target(raw, aliases)
            if page is None:
                continue
            checked += 1
            if page == "":
                page = stem
            if page not in pages:
                errors.append(f"page Markdown inexistante dans {path.name}: ({raw})")
            elif anchor and anchor not in anchor_cache[page]:
                errors.append(f"ancre Markdown absente dans {path.name}: ({raw})")

    print(f"Pages wiki contrôlées: {len(pages)}")
    print(f"Liens internes vérifiés: {checked}")
    if errors:
        for err in sorted(set(errors)):
            print("ERREUR:", err)
        return 1
    print("OK: pages, liens internes, ancres explicites et doublons d'ancres contrôlés.")
    print("NOTE: liens externes volontairement exclus du contrôle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
