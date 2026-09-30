#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Version helpers for Teamworks-CCNS.

The release train currently uses either final versions (``X.Y.Z``) or release
candidates (``X.Y.Z-rcN``).  Keep that grammar deliberately small and explicit
so update-related code does not silently reinterpret unknown version schemes.
"""

import re


_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-rc([1-9]\d*))?$", re.IGNORECASE)


def parse_version(version):
    """Return a tuple whose natural ordering follows the CCNS release order.

    Examples::

        0.9.2-rc1 < 0.9.2-rc2 < 0.9.2

    Unknown formats are rejected explicitly instead of being guessed.
    """
    if not isinstance(version, str):
        raise ValueError("Version Teamworks-CCNS invalide: %r" % (version,))

    value = version.strip()
    match = _VERSION_RE.fullmatch(value)
    if match is None:
        raise ValueError("Version Teamworks-CCNS invalide: %r" % value)

    major, minor, patch = (int(part) for part in match.group(1, 2, 3))
    rc = match.group(4)

    # A final release sorts after every release candidate of the same X.Y.Z.
    if rc is None:
        return major, minor, patch, 1, 0
    return major, minor, patch, 0, int(rc)


def read_version_file(path):
    """Read and validate a canonical VERSION file."""
    with open(path, "r", encoding="utf-8") as version_file:
        value = version_file.readline().strip()
    parse_version(value)
    return value


def read_first_valid_version(paths):
    """Return the first readable valid version, or ``None``.

    This is intended for UI code: a missing or malformed VERSION file must not
    turn the update menu into an unhandled exception.
    """
    for path in paths:
        try:
            return read_version_file(path)
        except (OSError, ValueError):
            continue
    return None
