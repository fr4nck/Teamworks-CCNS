#!/usr/bin/env python3
"""Migrate the final Python 2 standard-library imports to Python 3."""

from __future__ import annotations

import argparse
import tokenize
from pathlib import Path


TEAMWORD = Path("teamworks/Dlg/DLG_Teamword.py")
HTML2TEXT = Path("teamworks/Utils/UTILS_Html2text.py")
THUMBNAIL = Path("teamworks/Ctrl/CTRL_thumbnailctrl.py")


def read_source(path: Path) -> tuple[str, str]:
    with tokenize.open(path) as stream:
        return stream.read(), stream.encoding


def replace_exact(source: str, old: str, new: str, path: Path, expected: int) -> tuple[str, int]:
    matches = source.count(old)
    if matches not in (0, expected):
        raise SystemExit(f"Unexpected match count in {path}: {matches}, expected 0 or {expected}")
    if matches:
        source = source.replace(old, new)
    return source, matches


def migrate_teamword(root: Path, write: bool) -> int:
    path = root / TEAMWORD
    source, encoding = read_source(path)
    count = 0

    source, matches = replace_exact(
        source,
        "        import cStringIO\n        stream = cStringIO.StringIO()\n",
        "        import io\n        stream = io.BytesIO()\n",
        path,
        3,
    )
    count += matches

    source, matches = replace_exact(
        source,
        "        source = stream.getvalue()\n        head = \"\"\"",
        "        source = stream.getvalue().decode(\"utf-8\")\n        head = \"\"\"",
        path,
        2,
    )
    count += matches

    source, matches = replace_exact(
        source,
        "        source = source.replace(\"<head></head>\", head)\n        source = source.decode(\"utf-8\")\n",
        "        source = source.replace(\"<head></head>\", head)\n",
        path,
        2,
    )
    count += matches

    source, matches = replace_exact(
        source,
        "        texteHtml = stream.getvalue()\n        head = \"\"\"",
        "        texteHtml = stream.getvalue().decode(\"utf-8\")\n        head = \"\"\"",
        path,
        1,
    )
    count += matches

    source, matches = replace_exact(
        source,
        "        texteHtml = texteHtml.replace(\"<head></head>\", head)\n        texteHtml = texteHtml.decode(\"utf-8\")\n",
        "        texteHtml = texteHtml.replace(\"<head></head>\", head)\n",
        path,
        1,
    )
    count += matches

    if count and write:
        path.write_text(source, encoding=encoding, newline="")
    return count


def migrate_html2text(root: Path, write: bool) -> int:
    path = root / HTML2TEXT
    source, encoding = read_source(path)
    old = """try:\n    import htmlentitydefs\n    import urlparse\n    import HTMLParser\nexcept ImportError: #Python3\n    import html.entities as htmlentitydefs\n    from six.moves.urllib import parse as urlparse\n    import html.parser as HTMLParser\n"""
    new = """import html.entities as htmlentitydefs\nimport urllib.parse as urlparse\nimport html.parser as HTMLParser\n"""
    source, count = replace_exact(source, old, new, path, 1)
    if count and write:
        path.write_text(source, encoding=encoding, newline="")
    return count


def migrate_thumbnail(root: Path, write: bool) -> int:
    path = root / THUMBNAIL
    source, encoding = read_source(path)
    old = """if True:\n    import _thread as thread\nelse:\n    import thread\n"""
    new = "import _thread as thread\n"
    source, count = replace_exact(source, old, new, path, 1)
    if count and write:
        path.write_text(source, encoding=encoding, newline="")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    total = 0
    for migrate in (migrate_teamword, migrate_html2text, migrate_thumbnail):
        total += migrate(args.root, args.write)

    print(f"stdlib_import_migrations={total}")
    if args.check and total:
        raise SystemExit(f"{total} Python 2 standard-library migrations remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
