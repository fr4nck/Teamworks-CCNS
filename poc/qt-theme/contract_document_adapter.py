from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from application.services.contract_document_workspace import ContractDocumentContext
from application.services.document_template_catalog import discover_document_templates


def _date_text(value) -> str:
    if value in (None, ""):
        return ""
    formatter = getattr(value, "strftime", None)
    if callable(formatter):
        return formatter("%d/%m/%Y")
    return str(value)


def _decimal_text(value) -> str:
    if value in (None, ""):
        return ""
    return str(value)


class QtContractDocumentReadAdapter:
    """Port de lecture Documents pour le pilote Qt, sans dépendance PySide6."""

    METADATA_TABLE = "contrats_documents_modeles"

    def __init__(
        self,
        *,
        get_person_generalities: Callable[[int], object | None],
        contract_reader,
        db,
        template_directory: str | Path,
        structure_loader: Callable[[], Mapping[str, object]],
    ):
        self._get_person_generalities = get_person_generalities
        self._contract_reader = contract_reader
        self._db = db
        self._template_directory = Path(template_directory)
        self._structure_loader = structure_loader

    def load_context(self, contract_id: int) -> ContractDocumentContext | None:
        snapshot = self._contract_reader.read_contract(contract_id)
        if snapshot is None:
            return None

        person = self._get_person_generalities(snapshot.person_id)
        if person is None:
            return None

        phones = []
        emails = []
        for item in tuple(getattr(person, "coordinates", ()) or ()):
            category = str(getattr(item, "category", "") or "").strip()
            value = str(getattr(item, "text", "") or "").strip()
            if not value:
                continue
            if category in ("Fixe", "Mobile"):
                phones.append(value)
            elif category == "Email":
                emails.append(value)

        structure = dict(self._structure_loader() or {})
        employee = {
            "nom": getattr(person, "last_name", "") or "",
            "prenom": getattr(person, "first_name", "") or "",
            "civilite": getattr(person, "civility", "") or "",
            "date_naissance": getattr(person, "birth_date", "") or "",
            "adresse": getattr(person, "address", "") or "",
            "code_postal": getattr(person, "postcode", "") or "",
            "ville": getattr(person, "city", "") or "",
            "telephones": ", ".join(phones),
            "emails": ", ".join(emails),
        }
        contract = {
            "date_debut": _date_text(snapshot.start_date),
            "date_fin": _date_text(snapshot.end_date),
            "type": snapshot.contract_type_label or snapshot.contract_type_code or "",
            "classification": "",
            "convention": snapshot.convention_code or "",
            "groupe_ccns": snapshot.ccns_group or "",
            "duree_hebdo": _decimal_text(snapshot.weekly_hours),
            "salaire_brut_mensuel": _decimal_text(snapshot.gross_monthly_salary),
            "qualification_cee": snapshot.cee_qualification or "",
        }
        extra = {
            "CIVILITE": employee["civilite"],
            "NOM": employee["nom"],
            "PRENOM": employee["prenom"],
            "DATENAISS": employee["date_naissance"],
            "ADRESSERESID": employee["adresse"],
            "CPRESID": employee["code_postal"],
            "VILLERESID": employee["ville"],
            "TELEPHONES": employee["telephones"],
            "EMAILS": employee["emails"],
            "DATEDEBUT": contract["date_debut"],
            "DATEFIN": contract["date_fin"],
            "TYPECONTRAT": contract["type"],
            "CONVENTION": contract["convention"],
            "GROUPECCNS": contract["groupe_ccns"],
            "QUALIFICATIONCEE": contract["qualification_cee"],
            "DUREEHEBDO": contract["duree_hebdo"],
            "SALAIREBRUTMENSUEL": contract["salaire_brut_mensuel"],
        }
        return ContractDocumentContext(
            structure=structure,
            employee=employee,
            contract=contract,
            extra=extra,
        )

    def list_templates(self):
        return discover_document_templates(
            self._template_directory,
            metadata_loader=self._load_metadata,
        )

    def _load_metadata(self, filename: str):
        if not self._db.IsTableExists(self.METADATA_TABLE):
            return None

        fields = {
            str(item[0])
            for item in (self._db.GetListeChamps2(self.METADATA_TABLE) or ())
            if item
        }
        required = {
            "nom_fichier",
            "convention_code",
            "ccns_group",
            "cee_qualification",
        }
        if not required.issubset(fields):
            return None

        document_kind_expr = (
            "document_kind" if "document_kind" in fields else "NULL"
        )
        escaped = str(filename).replace("'", "''")
        req = (
            "SELECT convention_code, ccns_group, cee_qualification, %s "
            "FROM %s WHERE nom_fichier='%s';"
            % (document_kind_expr, self.METADATA_TABLE, escaped)
        )
        self._db.ExecuterReq(req)
        rows = self._db.ResultatReq()
        if not rows:
            return None
        convention_code, ccns_group, cee_qualification, document_kind = rows[0]
        return {
            "convention_code": convention_code or None,
            "ccns_group": ccns_group or None,
            "cee_qualification": cee_qualification or None,
            "document_kind": document_kind or None,
        }
