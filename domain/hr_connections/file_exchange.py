from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Iterable, Protocol, Tuple


class ExchangeDirection(str, Enum):
    """Sens d'un échange de fichier par rapport à Teamworks."""

    IMPORT = "import"
    EXPORT = "export"


class ValidationSeverity(str, Enum):
    """Gravité structurée d'une anomalie de format."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ExchangeFormat:
    """Format de fichier déclaré par un adaptateur RH."""

    code: str
    version: str
    media_type: str
    file_extension: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code du format d'échange est obligatoire.")
        if not self.version.strip():
            raise ValueError("La version du format d'échange est obligatoire.")
        if not self.media_type.strip() or "/" not in self.media_type:
            raise ValueError("Le type MIME du format d'échange est invalide.")
        if not self.file_extension.strip():
            raise ValueError("L'extension du format d'échange est obligatoire.")
        if any(separator in self.file_extension for separator in ("/", "\\")):
            raise ValueError("L'extension du format d'échange est invalide.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        version: str,
        media_type: str,
        file_extension: str,
    ) -> "ExchangeFormat":
        extension = file_extension.strip().lower()
        if extension.startswith("."):
            extension = extension[1:]
        return cls(
            code=code.strip(),
            version=version.strip(),
            media_type=media_type.strip().lower(),
            file_extension=extension,
        )


@dataclass(frozen=True)
class FileFingerprint:
    """Empreinte non secrète d'un fichier échangé."""

    algorithm: str
    digest: str

    def __post_init__(self) -> None:
        if self.algorithm != "sha256":
            raise ValueError("Seule l'empreinte SHA-256 est prise en charge à ce stade.")
        if len(self.digest) != 64:
            raise ValueError("L'empreinte SHA-256 doit contenir 64 caractères hexadécimaux.")
        try:
            int(self.digest, 16)
        except ValueError as exc:
            raise ValueError("L'empreinte SHA-256 est invalide.") from exc

    @classmethod
    def from_bytes(cls, payload: bytes) -> "FileFingerprint":
        if not isinstance(payload, bytes):
            raise TypeError("Le contenu à empreinter doit être fourni sous forme d'octets.")
        return cls(algorithm="sha256", digest=hashlib.sha256(payload).hexdigest())


@dataclass(frozen=True)
class ExchangeArtifact:
    """Métadonnées d'un fichier échangé, sans conserver son contenu."""

    artifact_id: str
    direction: ExchangeDirection
    adapter_id: str
    format_code: str
    file_name: str
    byte_size: int
    fingerprint: FileFingerprint
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not self.artifact_id.strip():
            raise ValueError("L'identifiant de l'artefact d'échange est obligatoire.")
        if not isinstance(self.direction, ExchangeDirection):
            raise TypeError("Le sens de l'échange est invalide.")
        if not self.adapter_id.strip():
            raise ValueError("L'identifiant de l'adaptateur est obligatoire.")
        if not self.format_code.strip():
            raise ValueError("Le code du format est obligatoire.")
        if not self.file_name.strip():
            raise ValueError("Le nom du fichier échangé est obligatoire.")
        if self.file_name in {".", ".."} or "/" in self.file_name or "\\" in self.file_name:
            raise ValueError("Le nom du fichier doit être un nom simple sans chemin.")
        if not isinstance(self.byte_size, int) or isinstance(self.byte_size, bool):
            raise TypeError("La taille du fichier échangé est invalide.")
        if self.byte_size < 0:
            raise ValueError("La taille du fichier échangé ne peut pas être négative.")
        if not isinstance(self.fingerprint, FileFingerprint):
            raise TypeError("L'empreinte du fichier échangé est invalide.")
        if not isinstance(self.occurred_at, datetime):
            raise TypeError("La date de l'échange est invalide.")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("La date de l'échange doit être associée à un fuseau horaire.")

    @classmethod
    def from_bytes(
        cls,
        *,
        artifact_id: str,
        direction: ExchangeDirection,
        adapter_id: str,
        exchange_format: ExchangeFormat,
        file_name: str,
        payload: bytes,
        occurred_at: datetime,
    ) -> "ExchangeArtifact":
        if not isinstance(exchange_format, ExchangeFormat):
            raise TypeError("Le format de l'artefact d'échange est invalide.")
        if not isinstance(payload, bytes):
            raise TypeError("Le contenu de l'artefact doit être fourni sous forme d'octets.")
        return cls(
            artifact_id=artifact_id.strip(),
            direction=direction,
            adapter_id=adapter_id.strip(),
            format_code=exchange_format.code,
            file_name=file_name.strip(),
            byte_size=len(payload),
            fingerprint=FileFingerprint.from_bytes(payload),
            occurred_at=occurred_at,
        )


@dataclass(frozen=True)
class ExchangeValidationIssue:
    """Anomalie structurée détectée lors de la validation d'un fichier."""

    code: str
    message: str
    severity: ValidationSeverity
    location: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Le code d'une anomalie d'échange est obligatoire.")
        if not self.message.strip():
            raise ValueError("Le message d'une anomalie d'échange est obligatoire.")
        if not isinstance(self.severity, ValidationSeverity):
            raise TypeError("La gravité d'une anomalie d'échange est invalide.")

    @classmethod
    def create(
        cls,
        *,
        code: str,
        message: str,
        severity: ValidationSeverity,
        location: str | None = None,
    ) -> "ExchangeValidationIssue":
        normalized_location = location.strip() if location is not None else None
        return cls(
            code=code.strip(),
            message=message.strip(),
            severity=severity,
            location=normalized_location or None,
        )


@dataclass(frozen=True)
class ExchangeValidationResult:
    """Résultat de validation sans exception pour les erreurs métier de fichier."""

    issues: Tuple[ExchangeValidationIssue, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if any(not isinstance(issue, ExchangeValidationIssue) for issue in self.issues):
            raise TypeError("La liste des anomalies d'échange est invalide.")

    @classmethod
    def ok(cls) -> "ExchangeValidationResult":
        return cls()

    @classmethod
    def from_issues(
        cls,
        issues: Iterable[ExchangeValidationIssue],
    ) -> "ExchangeValidationResult":
        return cls(issues=tuple(issues))

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity is ValidationSeverity.ERROR for issue in self.issues)

    @property
    def errors(self) -> Tuple[ExchangeValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is ValidationSeverity.ERROR)

    @property
    def warnings(self) -> Tuple[ExchangeValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is ValidationSeverity.WARNING)


@dataclass(frozen=True)
class FileExchangeDescriptor:
    """Description déclarative d'un adaptateur d'échange de fichiers."""

    adapter_id: str
    exchange_format: ExchangeFormat
    directions: FrozenSet[ExchangeDirection]

    def __post_init__(self) -> None:
        if not self.adapter_id.strip():
            raise ValueError("L'identifiant de l'adaptateur de fichier est obligatoire.")
        if not isinstance(self.exchange_format, ExchangeFormat):
            raise TypeError("Le format de l'adaptateur de fichier est invalide.")
        if not self.directions:
            raise ValueError("Un adaptateur de fichier doit annoncer au moins un sens d'échange.")
        if any(not isinstance(item, ExchangeDirection) for item in self.directions):
            raise TypeError("Un sens d'échange déclaré est invalide.")

    @classmethod
    def create(
        cls,
        *,
        adapter_id: str,
        exchange_format: ExchangeFormat,
        directions: Iterable[ExchangeDirection],
    ) -> "FileExchangeDescriptor":
        return cls(
            adapter_id=adapter_id.strip(),
            exchange_format=exchange_format,
            directions=frozenset(directions),
        )

    def supports(self, direction: ExchangeDirection) -> bool:
        return direction in self.directions


class FileExchangeAdapter(Protocol):
    """Frontière pure pour valider un fichier avant import ou export.

    L'adaptateur reçoit des octets déjà chargés par la couche appelante. Il n'ouvre
    pas de fichier, n'accède pas au réseau et ne persiste rien par ce contrat.
    """

    @property
    def descriptor(self) -> FileExchangeDescriptor:
        ...

    def validate(
        self,
        *,
        direction: ExchangeDirection,
        file_name: str,
        payload: bytes,
    ) -> ExchangeValidationResult:
        ...
