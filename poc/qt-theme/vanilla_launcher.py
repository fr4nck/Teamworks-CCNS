from __future__ import annotations

import os

os.environ.setdefault("TEAMWORKS_QT_SOURCE", "production")
os.environ.setdefault("TEAMWORKS_QT_APP_NAME", "Teamworks-CCNS Qt Vanilla")

from launcher import main


if __name__ == "__main__":
    main()
