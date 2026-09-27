"""Résolution READ ONLY des données Teamworks nécessaires à une DPAE.

DATA-001 : ce module ne fait ni migration, ni initialisation de configuration.
La connexion SQL injectée est utilisée exclusivement pour des SELECT et
Customize.ini est lu directement avec ConfigParser, sans UTILS_Customize.
"""
from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path

from application.services.dpae_service import DpaeBusinessData

# Cette version évolue seulement lorsqu'un mapping, une canonicalisation ou une
# règle d'interprétation modifie les données déclaratives produites.
DPAE_RULES_VERSION = "2026-09-27.2"


class DpaeBusinessDataMissing(ValueError):
    """Une donnée déclarative obligatoire ne peut pas être résolue."""


def _clean(value):
    return "" if value is None else str(value).strip()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TeamworksDpaeBusinessDataResolver:
    """Adaptateur ciblé du modèle historique Teamworks vers DpaeBusinessData.

    ``connection_factory`` retourne une connexion DB-API sur la base Teamworks.
    ``customize_path`` désigne le Customize.ini existant. Le fichier n'est
    jamais créé ni complété par ce resolver.
    """

    def __init__(self, connection_factory, customize_path):
        self._connect = connection_factory
        self._customize_path = Path(customize_path)

    def _organisation(self):
        cfg = configparser.ConfigParser()
        if self._customize_path.is_file():
            cfg.read(str(self._customize_path), encoding="utf-8")

        def get(key):
            if not cfg.has_section("organisation"):
                return ""
            return _clean(cfg.get("organisation", key, fallback=""))

        return {
            "raison_sociale": get("nom_officiel") or get("nom_usage"),
            "siren": get("siren"),
            "siret": get("siret"),
            "ape_naf": get("ape_naf"),
            "adresse": get("adresse"),
            "code_postal": get("code_postal"),
            "ville": get("ville"),
        }

    @staticmethod
    def _one(cur, sql, params, missing_code):
        cur.execute(sql, params)
        row = cur.fetchone()
        if row is None:
            raise DpaeBusinessDataMissing(missing_code)
        return row

    @staticmethod
    def _legacy_due_value(cur, code):
        """Lit une valeur déclarative mémorisée par le dialogue DUE historique.

        ``due_valeurs`` est un magasin global de valeurs de formulaire, pas une
        extension du contrat. La valeur n'est donc lue qu'au Prepare puis figée
        dans le Snapshot ; aucun retry/replay ne doit revenir à cette table.
        """
        cur.execute("SELECT valeur FROM due_valeurs WHERE code=%s", (code,))
        row = cur.fetchone()
        return _clean(row[0]) if row else ""

    def resolve(self, contract_id: str) -> DpaeBusinessData:
        conn = self._connect()
        try:
            cur = conn.cursor()
            contract = self._one(
                cur,
                "SELECT IDpersonne,IDtype,IDclassification,date_debut,date_fin,essai "
                "FROM contrats WHERE IDcontrat=%s",
                (contract_id,),
                "DPAE_CONTRACT_NOT_FOUND",
            )
            person_id, type_id, classification_id, date_debut, date_fin, essai = contract
            person = self._one(
                cur,
                "SELECT civilite,nom,nom_jfille,prenom,date_naiss,cp_naiss,ville_naiss,"
                "nationalite,num_secu,adresse_resid,cp_resid,ville_resid,pays_naiss "
                "FROM personnes WHERE IDpersonne=%s",
                (person_id,),
                "DPAE_PERSON_NOT_FOUND",
            )
            (civilite, nom, nom_jfille, prenom, date_naiss, cp_naiss, ville_naiss,
             nationality_id, num_secu, adresse, cp_resid, ville_resid, birth_country_id) = person

            contract_type = self._one(
                cur,
                "SELECT nom,nom_abrege,duree_indeterminee FROM contrats_types WHERE IDtype=%s",
                (type_id,),
                "DPAE_CONTRACT_TYPE_NOT_FOUND",
            )
            classification = self._one(
                cur,
                "SELECT nom FROM contrats_class WHERE IDclassification=%s",
                (classification_id,),
                "DPAE_CLASSIFICATION_NOT_FOUND",
            )[0]

            nationality = ""
            if nationality_id not in (None, ""):
                cur.execute("SELECT nationalite FROM pays WHERE IDpays=%s", (nationality_id,))
                row = cur.fetchone()
                nationality = _clean(row[0]) if row else ""
            birth_country = ""
            if birth_country_id not in (None, ""):
                cur.execute("SELECT nom FROM pays WHERE IDpays=%s", (birth_country_id,))
                row = cur.fetchone()
                birth_country = _clean(row[0]) if row else ""

            # Le dialogue legacy DLG_Edition_DUE mémorise HEURE_EMBAUCHE dans
            # due_valeurs à chaque édition. C'est une donnée déclarative globale
            # réutilisée par la DUE suivante, et non une colonne du contrat.
            hiring_time = self._legacy_due_value(cur, "HEURE_EMBAUCHE")
        finally:
            conn.close()

        organisation = self._organisation()
        if not organisation["siret"]:
            raise DpaeBusinessDataMissing("DPAE_EMPLOYER_SIRET_MISSING")

        civilite = _clean(civilite)
        if civilite == "Mr":
            sex, birth_name, married_name = "M", _clean(nom), ""
        elif civilite in ("Mme", "Melle"):
            sex = "F"
            birth_name = _clean(nom_jfille) or _clean(nom)
            married_name = _clean(nom) if civilite == "Mme" else ""
        else:
            sex, birth_name, married_name = "", _clean(nom), ""

        cp_naiss = _clean(cp_naiss)
        payload = {
            "contract": {
                "contract_id": str(contract_id),
                "start_date": _clean(date_debut),
                "hiring_time": hiring_time or None,
                "end_date": _clean(date_fin),
                "trial_period": _clean(essai),
                "type": _clean(contract_type[0]),
                "type_short": _clean(contract_type[1]),
                "indefinite": _clean(contract_type[2]),
                "classification": _clean(classification),
            },
            "employee": {
                # IDpersonne sert uniquement à résoudre la personne. C'est un
                # identifiant technique Teamworks, pas une donnée déclarative :
                # il ne doit donc influencer ni snapshot ni fingerprint.
                "birth_name": birth_name,
                "married_name": married_name,
                "first_names": _clean(prenom),
                "sex": sex,
                "nir": _clean(num_secu).replace(" ", ""),
                "birth_date": _clean(date_naiss),
                "birth_department": cp_naiss[:2] if cp_naiss else "",
                "birth_city": _clean(ville_naiss),
                "birth_country": birth_country,
                "nationality": nationality,
                "address": _clean(adresse),
                "postal_code": _clean(cp_resid),
                "city": _clean(ville_resid),
            },
            "employer": organisation,
        }
        canonical_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        source_projection = json.dumps(
            {"rules_version": DPAE_RULES_VERSION, "data": payload},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return DpaeBusinessData(
            contract_id=str(contract_id),
            canonical_payload=canonical_payload,
            source_fingerprint=_sha256(source_projection),
            rules_version=DPAE_RULES_VERSION,
            payload_hash=_sha256(canonical_payload),
        )
