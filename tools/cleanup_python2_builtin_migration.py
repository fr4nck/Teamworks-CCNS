#!/usr/bin/env python3
"""Clean redundant constructs produced by the Python 2 builtin migration."""

from __future__ import annotations

import argparse
import io
import tokenize
from pathlib import Path


REPLACEMENTS = (
    ("(int, float, int)", "(int, float)"),
    ("(int, int, float)", "(int, float)"),
    ("type(self.fichierImageSource) == str or type(self.fichierImageSource) == str", "isinstance(self.fichierImageSource, str)"),
    ("if six.PY2:\n            self.typeToFunctionMap[int] = self._MakeIntegerEditor\n            self.typeToFunctionMap[int] = self._MakeLongEditor\n        else:\n            self.typeToFunctionMap[int] = self._MakeLongEditor", "self.typeToFunctionMap[int] = self._MakeLongEditor"),
    ("self.outtext = str()\n        except NameError: # Python3\n            self.outtext = str()", "self.outtext = str()\n        except NameError: # Python3\n            self.outtext = str()"),
)


def iter_python_files(path: Path):
    if path.is_file():
        yield path
    else:
        yield from sorted(path.rglob("*.py"))


def detect_encoding(raw: bytes) -> str:
    return tokenize.detect_encoding(io.BytesIO(raw).readline)[0]


def migrate_file(path: Path, write: bool) -> int:
    raw = path.read_bytes()
    encoding = detect_encoding(raw)
    text = raw.decode(encoding)
    count = 0
    for old, new in REPLACEMENTS:
        occurrences = text.count(old)
        if occurrences:
            text = text.replace(old, new)
            count += occurrences
    if write and count:
        path.write_bytes(text.encode(encoding))
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="teamworks")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    total = 0
    changed = 0
    for path in iter_python_files(Path(args.path)):
        count = migrate_file(path, args.write)
        if count:
            changed += 1
            total += count
            print(f"{path}: {count}")

    action = "cleaned" if args.write else "would clean"
    print(f"{action} {total} construct(s) in {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
