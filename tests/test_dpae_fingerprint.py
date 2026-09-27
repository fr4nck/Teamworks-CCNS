from datetime import date

from domain.dpae.fingerprint import DPAE_RULES_VERSION,DpaeSourceProjection,compute_source_fingerprint


def _source(**changes):
    values={"contract_id":"742","hiring_date":date(2026,10,19),"employer_siret":"12345678901234","employee_fields":{"last_name":"Martin","first_name":"Alice"},"contract_fields":{},"employer_fields":{}}
    values.update(changes); return DpaeSourceProjection(**values)


def test_source_fingerprint_is_deterministic(): assert compute_source_fingerprint(_source())==compute_source_fingerprint(_source())


def test_source_fingerprint_changes_when_declarative_contract_data_changes():
    before=compute_source_fingerprint(_source()); after=compute_source_fingerprint(_source(contract_fields={"type":"CDD"})); assert before!=after


def test_source_fingerprint_changes_when_rules_change():
    source=_source(); before=compute_source_fingerprint(source); after=compute_source_fingerprint(source,rules_version="2026-09-27.2"); assert DPAE_RULES_VERSION=="2026-09-27.1"; assert before!=after


def test_mapping_order_does_not_change_fingerprint():
    first=_source(employee_fields={"last_name":"Martin","first_name":"Alice"}); second=_source(employee_fields={"first_name":"Alice","last_name":"Martin"}); assert compute_source_fingerprint(first)==compute_source_fingerprint(second)
