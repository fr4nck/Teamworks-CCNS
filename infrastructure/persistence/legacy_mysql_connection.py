"""MySQL connection factory with no dependency on Teamworks GUI or DB globals.

The legacy connector implementations are supplied by the integration layer.
Opening a connection does not select a database or commit a transaction.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, MutableMapping

from infrastructure.persistence.legacy_network_target import LegacyNetworkTarget


def open_legacy_mysql(
    target: LegacyNetworkTarget,
    *,
    driver: str,
    decode_password: Callable[[str], str],
    certificates: Mapping[str, str] | None = None,
    mysql_connector: Any = None,
    mysqldb_driver: Any = None,
    connector_options: Callable[..., dict[str, Any]] | None = None,
    connector_diagnostic: Callable[..., str] | None = None,
    mysqldb_conversions: MutableMapping[Any, Any] | None = None,
    mysqldb_long_field: Any = None,
) -> tuple[Any, str]:
    """Connect via a selected legacy driver and return (connection, database).

    Keep existing MySQL 5.5-compatible options and the historical MySQLdb
    converter/UTF-8 setup. No wx/Qt import, file access, SQL or implicit commit.
    Password decoding is injected and performed once per connection.
    """
    if not isinstance(target, LegacyNetworkTarget):
        raise TypeError("A parsed legacy network target is required")
    if driver not in ("mysql.connector", "mysqldb"):
        raise ValueError("Unsupported MySQL interface")

    if driver == "mysql.connector":
        if mysql_connector is None or connector_options is None or connector_diagnostic is None:
            raise RuntimeError("mysql.connector is unavailable")
    elif mysqldb_driver is None or mysqldb_conversions is None or mysqldb_long_field is None:
        raise RuntimeError("MySQLdb is unavailable")

    password = decode_password(target.password_token)
    certs = certificates if certificates is not None else {}

    if driver == "mysql.connector":
        options = connector_options(
            target.host, target.user, password, target.port, certs
        )
        try:
            connection = mysql_connector.connect(**options)
        except Exception as exc:
            version = getattr(mysql_connector, "__version__", "inconnue")
            diagnostic = connector_diagnostic(
                exc, target.host, target.port, driver, version
            )
            raise RuntimeError(diagnostic) from exc
        return connection, target.database

    # The historical MySQLdb adapter mutates the shared conversions mapping.
    # Keep that contract for old connector versions and their LONG handling.
    mysqldb_conversions[mysqldb_long_field] = int
    connection = mysqldb_driver.connect(
        host=target.host,
        user=target.user,
        passwd=password,
        port=target.port,
        use_unicode=True,
        conv=mysqldb_conversions,
        ssl=certs,
    )
    try:
        connection.set_character_set("utf8")
    except Exception:
        # Avoid leaking a connection when the legacy encoding setup fails.
        try:
            connection.close()
        except Exception:
            pass
        raise
    return connection, target.database
