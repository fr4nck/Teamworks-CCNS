"""Decode a legacy Teamworks network database reference without UI imports.

The on-disk format is port;host;user;password[RESEAU]database. Its password
field is opaque and may use the historical #64# prefix. Decoding that token
and opening a connection belong to a driver adapter, not this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field


NETWORK_MARKER = "[RESEAU]"


@dataclass(frozen=True, slots=True)
class LegacyNetworkTarget:
    port: int
    host: str
    user: str
    password_token: str = field(repr=False)
    database: str

    def as_legacy_parameters(self) -> dict[str, str | int]:
        """Preserve the keys exposed by GestionDB.GetParamConnexionReseau."""
        return {
            "port": self.port,
            "hote": self.host,
            "host": self.host,
            "user": self.user,
            "utilisateur": self.user,
            "mdp": self.password_token,
            "password": self.password_token,
            "fichier": self.database,
        }


def parse_legacy_network_target(reference: str) -> LegacyNetworkTarget:
    """Parse the historical reference, preserving its established semantics.

    The database name is lowercased as before. The password is not decoded,
    and neither the input nor the secret is included in exceptions or repr.
    Invalid references fail before any database connection is attempted.
    """
    if not isinstance(reference, str):
        raise TypeError("Network reference must be a string")
    pos = reference.find(NETWORK_MARKER)
    if pos < 0:
        raise ValueError("Missing legacy network marker")
    parts = reference[:pos].split(";")
    if len(parts) != 4:
        raise ValueError("Invalid legacy network connection field count")
    port_text, host, user, password_token = parts
    try:
        port = int(port_text)
    except ValueError:
        raise ValueError("Invalid legacy network port") from None
    database = reference[pos:].replace(NETWORK_MARKER, "").lower()
    return LegacyNetworkTarget(port, host, user, password_token, database)
