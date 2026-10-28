"""Read the selected legacy database without importing a UI toolkit.

This persistence boundary reads the existing Config.json format. The UI
chooses a database; the engine only receives its name (explicitly or via the
configuration file). No wxPython or PySide6 dependency belongs here.
"""

from __future__ import annotations

import json
from os import PathLike


def read_current_database_name(config_path: str | PathLike[str]) -> str:
    """Return the configured database name, or an empty string if unusable.

    Keep the original name intact: it can contain the historical network
    connection format as well as a local database name. No database is opened
    and no configuration is created or modified by this function.
    """
    try:
        with open(config_path, encoding="utf-8") as stream:
            config = json.load(stream)
    except (OSError, ValueError, UnicodeError, TypeError):
        return ""
    if not isinstance(config, dict):
        return ""
    name = config.get("nomFichier")
    return name if isinstance(name, str) else ""
