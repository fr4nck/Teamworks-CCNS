from __future__ import annotations

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping


CURRENT_DOCUMENT_FORMAT_VERSION = 1
SUPPORTED_DOCUMENT_FORMAT_VERSIONS = (CURRENT_DOCUMENT_FORMAT_VERSION,)


class DocumentFormatError(ValueError):
    """Raised when a serialized document does not respect the canonical contract."""


def _assert_json_compatible(value: Any, path: str = "value") -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_json_compatible(item, f"{path}[{index}]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_json_compatible(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise DocumentFormatError(f"{path}: JSON object keys must be strings")
            _assert_json_compatible(item, f"{path}.{key}")
        return
    raise DocumentFormatError(f"{path}: unsupported non-JSON value {type(value).__name__}")


def _new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class DocumentMetadata:
    title: str = ""
    owner_domain: str = "rh"
    language: str = "fr-FR"
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.owner_domain.strip():
            raise DocumentFormatError("metadata.owner_domain must identify a business domain")
        _assert_json_compatible(self.attributes, "metadata.attributes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "owner_domain": self.owner_domain,
            "language": self.language,
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentMetadata":
        return cls(
            title=str(payload.get("title", "")),
            owner_domain=str(payload.get("owner_domain", "rh")),
            language=str(payload.get("language", "fr-FR")),
            attributes=dict(payload.get("attributes") or {}),
        )


@dataclass(frozen=True)
class Asset:
    id: str
    mime_type: str
    name: str
    content_base64: str
    sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.id)
        except (ValueError, AttributeError) as exc:
            raise DocumentFormatError(f"Invalid asset id: {self.id!r}") from exc
        if str(parsed) != self.id.lower():
            object.__setattr__(self, "id", str(parsed))
        if not self.mime_type or "/" not in self.mime_type:
            raise DocumentFormatError("asset.mime_type must be a MIME type")
        try:
            raw = base64.b64decode(self.content_base64.encode("ascii"), validate=True)
        except Exception as exc:
            raise DocumentFormatError("asset.content_base64 is not valid base64") from exc
        digest = hashlib.sha256(raw).hexdigest()
        if digest != self.sha256:
            raise DocumentFormatError("asset.sha256 does not match embedded content")
        _assert_json_compatible(self.metadata, "asset.metadata")

    @property
    def uri(self) -> str:
        return f"asset://{self.id}"

    def to_bytes(self) -> bytes:
        return base64.b64decode(self.content_base64.encode("ascii"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "mime_type": self.mime_type,
            "name": self.name,
            "content_base64": self.content_base64,
            "sha256": self.sha256,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_bytes(
        cls,
        *,
        content: bytes,
        mime_type: str,
        name: str,
        asset_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Asset":
        digest = hashlib.sha256(content).hexdigest()
        return cls(
            id=asset_id or _new_uuid(),
            mime_type=mime_type,
            name=name,
            content_base64=base64.b64encode(content).decode("ascii"),
            sha256=digest,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Asset":
        return cls(
            id=str(payload["id"]),
            mime_type=str(payload["mime_type"]),
            name=str(payload.get("name", "")),
            content_base64=str(payload["content_base64"]),
            sha256=str(payload["sha256"]),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass(frozen=True)
class DocumentModel:
    id: str
    format_version: int
    document_type: str
    html: str
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    assets: tuple[Asset, ...] = ()
    render_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.id)
        except (ValueError, AttributeError) as exc:
            raise DocumentFormatError(f"Invalid document id: {self.id!r}") from exc
        if str(parsed) != self.id.lower():
            object.__setattr__(self, "id", str(parsed))
        if self.format_version not in SUPPORTED_DOCUMENT_FORMAT_VERSIONS:
            raise DocumentFormatError(
                f"Unsupported document format_version {self.format_version}; "
                f"supported={SUPPORTED_DOCUMENT_FORMAT_VERSIONS}"
            )
        if not self.document_type.strip():
            raise DocumentFormatError("document_type must not be empty")
        _assert_json_compatible(self.render_options, "render_options")
        asset_ids = [asset.id for asset in self.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise DocumentFormatError("Duplicate asset ids are not allowed")

    @classmethod
    def create(
        cls,
        *,
        document_type: str,
        html: str,
        metadata: DocumentMetadata | None = None,
        assets: tuple[Asset, ...] | list[Asset] = (),
        render_options: Mapping[str, Any] | None = None,
        document_id: str | None = None,
    ) -> "DocumentModel":
        return cls(
            id=document_id or _new_uuid(),
            format_version=CURRENT_DOCUMENT_FORMAT_VERSION,
            document_type=document_type,
            html=html,
            metadata=metadata or DocumentMetadata(),
            assets=tuple(assets),
            render_options=dict(render_options or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "format_version": self.format_version,
            "document_type": self.document_type,
            "html": self.html,
            "metadata": self.metadata.to_dict(),
            "assets": [asset.to_dict() for asset in self.assets],
            "render_options": dict(self.render_options),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentModel":
        version = int(payload.get("format_version", 0))
        if version not in SUPPORTED_DOCUMENT_FORMAT_VERSIONS:
            raise DocumentFormatError(
                f"Unsupported document format_version {version}; "
                f"supported={SUPPORTED_DOCUMENT_FORMAT_VERSIONS}"
            )
        return cls(
            id=str(payload["id"]),
            format_version=version,
            document_type=str(payload["document_type"]),
            html=str(payload.get("html", "")),
            metadata=DocumentMetadata.from_dict(payload.get("metadata") or {}),
            assets=tuple(Asset.from_dict(item) for item in (payload.get("assets") or [])),
            render_options=dict(payload.get("render_options") or {}),
        )

    @classmethod
    def from_json(cls, raw: str) -> "DocumentModel":
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise DocumentFormatError("Serialized document root must be a JSON object")
        return cls.from_dict(payload)
