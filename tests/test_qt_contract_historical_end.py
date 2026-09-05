from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from infrastructure.persistence.ccns_data_reader import CcnsDataReader


ROOT = Path(__file__).resolve().parents[1]
POC = ROOT / "poc" / "qt-theme"
EXAMPLE_DB = ROOT / "teamworks" / "Static" / "Exemples" / "Exemple_TDATA.dat"
if str(POC) not in sys.path:
    sys.path.insert(0, str(POC))

from production_read_adapter import TeamworksProductionReadAdapter


class SqliteGestionDBCompat:
    def __init__(self, path: Path):
        self._connection = sqlite3.connect(path)
        self._cursor = None

    def ExecuterReq(self, req):
        self._cursor = self._connection.execute(req)

    def ResultatReq(self):
        return self._cursor.fetchall()

    def Close(self):
        self._connection.close()


def test_contract_reader_projects_historical_break_date_from_example_database():
    db = SqliteGestionDBCompat(EXAMPLE_DB)
    reader = CcnsDataReader(db_factory=lambda: db)

    records = reader.lire_contrats_personne(6)
    broken = next(record for record in records if record.IDcontrat == 9)

    assert broken.date_debut == "2011-12-01"
    assert broken.date_fin == "2012-08-31"
    assert broken.date_rupture == "2011-12-27"

    reader.close()


def test_qt_contract_mapping_prioritizes_historical_break_date_over_planned_end():
    db = SqliteGestionDBCompat(EXAMPLE_DB)
    reader = CcnsDataReader(db_factory=lambda: db)
    records = reader.lire_contrats_personne(6)
    broken = next(record for record in records if record.IDcontrat == 9)

    view = TeamworksProductionReadAdapter._contract_to_view(broken)

    assert view.end == "27/12/2011-R"
    assert view.end != "31/08/2012"

    reader.close()
