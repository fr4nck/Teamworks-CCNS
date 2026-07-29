#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prépare, vérifie ou restaure un profil d'affichage Teamworks-CCNS."""

from __future__ import annotations

import argparse
import configparser
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

THEMES = {
    "systeme": "Systeme",
    "système": "Systeme",
    "system": "Systeme",
    "auto": "Systeme",
    "clair": "Clair",
    "light": "Clair",
    "blanc": "Clair",
    "sombre": "Sombre",
    "dark": "Sombre",
    "noir": "Sombre",
}
MIN_SCALE = 80
MAX_SCALE = 200


def normalize_theme(value: str) -> str:
    try:
        return THEMES[value.strip().lower()]
    except KeyError as exc:
        raise ValueError(
            f"Thème invalide : {value!r}. Valeurs admises : Système, Clair ou Sombre."
        ) from exc


def normalize_scale(value: int) -> int:
    if not MIN_SCALE <= value <= MAX_SCALE:
        raise ValueError(
            f"Échelle invalide : {value}. Valeurs admises : {MIN_SCALE} à {MAX_SCALE} %."
        )
    return value


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = path.with_name(f"{path.name}.tw121-{timestamp}.bak")
    shutil.copy2(path, backup)
    return backup


def _decode_config(raw: bytes) -> tuple[str, str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"

    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("cp1252"), "cp1252"


def _load_config(path: Path) -> tuple[configparser.ConfigParser, str]:
    if not path.is_file():
        raise ValueError(f"Configuration introuvable : {path}")

    try:
        text, encoding = _decode_config(path.read_bytes())
        parser = configparser.ConfigParser()
        parser.read_string(text)
        return parser, encoding
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise ValueError(f"Configuration illisible : {path}") from exc


def read_profile(path: Path) -> tuple[str, int]:
    parser, _encoding = _load_config(path)
    if not parser.has_section("interface"):
        raise ValueError("Section [interface] absente de la configuration")

    try:
        theme = normalize_theme(parser.get("interface", "theme"))
        scale = normalize_scale(parser.getint("interface", "echelle_police"))
    except (configparser.Error, ValueError) as exc:
        raise ValueError("Profil d'affichage incomplet ou invalide") from exc
    return theme, scale


def verify_profile(path: Path, expected_theme: str, expected_scale: int) -> None:
    expected = (normalize_theme(expected_theme), normalize_scale(expected_scale))
    actual = read_profile(path)
    if actual != expected:
        raise ValueError(
            "Persistance invalide : "
            f"attendu {expected[0]} / {expected[1]} %, "
            f"relu {actual[0]} / {actual[1]} %"
        )


def _replace_atomic(path: Path, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream, source.open("rb") as origin:
            shutil.copyfileobj(origin, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_atomic(
    path: Path, parser: configparser.ConfigParser, encoding: str = "utf-8"
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding) as stream:
            parser.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def apply_profile(path: Path, theme: str, scale: int) -> Path | None:
    theme = normalize_theme(theme)
    scale = normalize_scale(scale)

    if path.exists():
        parser, encoding = _load_config(path)
    else:
        parser = configparser.ConfigParser()
        encoding = "utf-8"

    if not parser.has_section("interface"):
        parser.add_section("interface")

    backup = backup_file(path)
    parser.set("interface", "theme", theme)
    parser.set("interface", "echelle_police", str(scale))
    _write_atomic(path, parser, encoding)
    verify_profile(path, theme, scale)
    return backup


def restore_backup(path: Path, backup: Path) -> tuple[str, int]:
    if not backup.is_file():
        raise ValueError(f"Sauvegarde introuvable : {backup}")

    expected = read_profile(backup)
    _replace_atomic(path, backup)
    actual = read_profile(path)
    if actual != expected:
        raise ValueError("Restauration invalide : le profil relu diffère de la sauvegarde")
    return actual


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prépare, vérifie ou restaure Customize.ini pour TW-123."
    )
    parser.add_argument("config", type=Path, help="Chemin explicite vers Customize.ini")
    parser.add_argument("--theme", help="Système, Clair ou Sombre")
    parser.add_argument("--scale", type=int, help="Échelle de police entre 80 et 200")
    parser.add_argument("--check-only", action="store_true", help="Vérifie sans modifier")
    parser.add_argument("--restore", type=Path, help="Restaure une sauvegarde .bak explicite")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.restore:
            if args.check_only or args.theme is not None or args.scale is not None:
                raise ValueError("--restore ne peut pas être combiné avec un profil ou --check-only")
            theme, scale = restore_backup(args.config, args.restore)
            print(f"Profil restauré et relu : {theme} / {scale} %")
            print(f"Configuration : {args.config}")
            return 0

        if args.theme is None or args.scale is None:
            raise ValueError("--theme et --scale sont requis hors restauration")

        if args.check_only:
            verify_profile(args.config, args.theme, args.scale)
            print(f"Profil confirmé : {normalize_theme(args.theme)} / {args.scale} %")
            print(f"Configuration : {args.config}")
            return 0

        backup = apply_profile(args.config, args.theme, args.scale)
    except (OSError, ValueError) as exc:
        print(f"ERREUR : {exc}")
        return 2

    print(f"Profil appliqué et relu : {normalize_theme(args.theme)} / {args.scale} %")
    print(f"Configuration : {args.config}")
    if backup:
        print(f"Sauvegarde : {backup}")
    else:
        print("Sauvegarde : aucune, le fichier n'existait pas")
    print("Relancer Teamworks-CCNS pour appliquer le profil.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
