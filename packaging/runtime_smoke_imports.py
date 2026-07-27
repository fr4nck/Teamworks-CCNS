# -*- coding: utf-8 -*-
"""PyInstaller runtime hook used by CI to validate packaged dynamic imports."""

import os


if os.environ.get("TEAMWORKS_PACKAGED_SMOKE_TEST") == "1":
    import Gadget  # noqa: F401
    from Ctrl import CTRL_Accueil  # noqa: F401
    from Utils import UTILS_Adaptations  # noqa: F401
    from Dlg import DLG_Saisie_question  # noqa: F401
    from Ol import OL_candidatures  # noqa: F401
    from CcnsCore import runtime_bridge  # noqa: F401
    from domain.repositories import ccns_data  # noqa: F401
    from infrastructure.persistence import ccns_data_reader  # noqa: F401

    raise SystemExit(0)
