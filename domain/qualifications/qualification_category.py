"""Catégories métier d'une qualification."""

from enum import Enum


class QualificationCategory(str, Enum):
    """Nature de la qualification définie dans le référentiel."""

    DIPLOMA = "DIPLOMA"
    CERTIFICATION = "CERTIFICATION"
    AUTHORIZATION = "AUTHORIZATION"
    TRAINING = "TRAINING"
    LICENSE = "LICENSE"
    OTHER = "OTHER"
