import hashlib
import json

import pytest

from infrastructure.dpae_teamworks_resolver import (
    DpaeBusinessDataMissing,
    TeamworksDpaeBusinessDataResolver,
)


class Cursor:
    def __init__(self):
        self.row = None
        self.sql = []

    def execute(self, sql, params):
        self.sql.append(sql)
        normalized = " ".join(sql.split()).lower()
        assert normalized.startswith("select ")
        if " from contrats where " in normalized:
            self.row = (18, 2, 3, "2026-10-15", "2027-10-14", 7)
        elif " from personnes where " in normalized:
            self.row = ("Mme", "Martin", "Durand", "Alice", "1990-02-03", "35000", "Rennes", 1, "", "1 rue X", "35650", "Le Rheu", 33)
        elif " from contrats_types where " in normalized:
            self.row = ("CDD", "CDD", "non")
        elif " from contrats_class where " in normalized:
            self.row = ("Groupe B",)
        elif "select nationalite from pays" in normalized:
            self.row = ("Française",)
        elif "select nom from pays" in normalized:
            self.row = ("France",)
        else:
            raise AssertionError(sql)

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self):
        self.cur = Cursor(); self.closed = False
    def cursor(self): return self.cur
    def close(self): self.closed = True


def make_resolver(tmp_path, ini=True):
    path = tmp_path / "Customize.ini"
    if ini:
        path.write_text("[organisation]\nnom_officiel=Association Test\nsiret=12345678901234\nsiren=123456789\nape_naf=9499Z\nadresse=2 rue Y\ncode_postal=35650\nville=Le Rheu\n", encoding="utf-8")
    connections = []
    def connect():
        c = Connection(); connections.append(c); return c
    return TeamworksDpaeBusinessDataResolver(connect, path), path, connections


def test_resolver_reads_real_legacy_sources_without_sql_mutation_or_config_write(tmp_path):
    resolver, path, connections = make_resolver(tmp_path)
    before = path.read_bytes(); before_hash = hashlib.sha256(before).hexdigest()
    data = resolver.resolve("742")
    assert path.read_bytes() == before
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before_hash
    assert all(sql.lstrip().upper().startswith("SELECT ") for sql in connections[0].cur.sql)
    payload = json.loads(data.canonical_payload)
    assert payload["contract"]["contract_id"] == "742"
    assert payload["contract"]["hiring_time"] is None
    assert "person_id" not in payload["employee"]
    assert payload["employee"]["birth_name"] == "Durand"
    assert payload["employee"]["sex"] == "F"
    assert payload["employer"]["siret"] == "12345678901234"
    assert data.payload_hash == hashlib.sha256(data.canonical_payload.encode("utf-8")).hexdigest()
    assert data.source_fingerprint != data.payload_hash


def test_missing_customize_is_not_created(tmp_path):
    resolver, path, _ = make_resolver(tmp_path, ini=False)
    assert not path.exists()
    with pytest.raises(DpaeBusinessDataMissing, match="DPAE_EMPLOYER_SIRET_MISSING"):
        resolver.resolve("742")
    assert not path.exists()


def test_missing_organisation_section_is_not_added(tmp_path):
    resolver, path, _ = make_resolver(tmp_path, ini=False)
    path.write_text("[interface]\nappearance=system\n", encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(DpaeBusinessDataMissing, match="DPAE_EMPLOYER_SIRET_MISSING"):
        resolver.resolve("742")
    assert path.read_bytes() == before
