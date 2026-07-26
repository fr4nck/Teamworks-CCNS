from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "teamworks" / "GestionDB.py"


def test_creation_table_builds_complete_sql_before_execution():
    source = SOURCE.read_text(encoding="iso-8859-15")
    start = source.index("    def CreationTable(self, nomTable=\"\", dicoDB={}):")
    end = source.index("    def ExecuterReq(self, req):", start)
    block = source[start:end]

    append_index = block.index('req += "%s %s, " % (nomChamp, typeChamp)')
    finalize_index = block.index('req = req[:-2] + ")"')
    execute_index = block.index("self.cursor.execute(req)")

    assert append_index < finalize_index < execute_index
    assert 'self.cursor.execute(req)' not in block[:finalize_index]
    assert 'GestionDB.CreationTable' in block
