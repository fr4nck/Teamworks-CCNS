"""Gravité des anomalies de migration, indépendante de l'UI."""

from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    INFO = "INFO"
    REVIEW = "REVIEW"
    BLOCKING = "BLOCKING"
