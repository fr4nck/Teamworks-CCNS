from __future__ import annotations

from enum import Enum


class ConnectorCapability(str, Enum):
    """Capacités qu'un connecteur RH peut annoncer explicitement."""

    DEEP_LINK = "deep_link"
    DOCUMENT_IMPORT = "document_import"
    DOCUMENT_EXPORT = "document_export"
    API = "api"
    STATUS_SYNC = "status_sync"
    SUBMISSION = "submission"
    DOCUMENT_DOWNLOAD = "document_download"
    MANUAL_STATUS = "manual_status"


class ConnectorMode(str, Enum):
    """Modes d'intégration disponibles pour un connecteur."""

    MANUAL = "manual"
    FILE = "file"
    API = "api"


class ConnectorState(str, Enum):
    """État d'exposition d'un connecteur dans Teamworks."""

    AVAILABLE = "available"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"
    NOT_CONFIGURED = "not_configured"
