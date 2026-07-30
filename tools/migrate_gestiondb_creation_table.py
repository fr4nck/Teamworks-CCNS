#!/usr/bin/env python3
"""Restore the column-building logic of GestionDB.CreationTable."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "teamworks" / "GestionDB.py"

FIXED = '''    def CreationTable(self, nomTable="", dicoDB={}):
        req = "CREATE TABLE %s (" % nomTable
        for descr in dicoDB[nomTable]:
            nomChamp = descr[0]
            typeChamp = descr[1]
            # Adaptation à SQLite
            if self.isNetwork == False and typeChamp == "LONGBLOB":
                typeChamp = "BLOB"
            if self.isNetwork == False and typeChamp == "BIGINT":
                typeChamp = "INTEGER"
            # Adaptation à MySQL
            if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT":
                typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
            if self.isNetwork == True and typeChamp == "FLOAT":
                typeChamp = "REAL"
            if self.isNetwork == True and typeChamp == "DATE":
                typeChamp = "VARCHAR(10)"
            if self.isNetwork == True and typeChamp.startswith("VARCHAR"):
                nbreCaract = int(typeChamp[typeChamp.find("(") + 1:typeChamp.find(")")])
                if nbreCaract > 255:
                    typeChamp = "TEXT(%d)" % nbreCaract
                if nbreCaract > 20000:
                    typeChamp = "MEDIUMTEXT"
            req += "%s %s, " % (nomChamp, typeChamp)
        req = req[:-2] + ")"
        with DiagnosticPerformance.mesurer("sql", "GestionDB.CreationTable", {"requete": req[:160]}):
            self.cursor.execute(req)

'''

PATTERN = re.compile(
    r"    def CreationTable\(self, nomTable=\"\", dicoDB=\{\}\):\n.*?(?=    def ExecuterReq\(self, req\):)",
    re.DOTALL,
)


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    if FIXED in source:
        print("GestionDB.CreationTable already repaired")
        return 0

    matches = list(PATTERN.finditer(source))
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one CreationTable method before ExecuterReq, found {len(matches)}"
        )

    repaired = PATTERN.sub(FIXED, source, count=1)
    TARGET.write_text(repaired, encoding="utf-8")
    print(f"updated {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
