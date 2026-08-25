#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:       Licence GNU GPL
#-----------------------------------------------------------

import datetime
from decimal import Decimal

from Utils.UTILS_Traduction import _
from Utils import UTILS_Contrats_schema, UTILS_CEE_baremes
import wx
import FonctionsPerso
import GestionDB

from application.control.contract_compensation_preflight import (
    ContractCompensationPreflight,
    validate_cee_daily_compensation,
    validate_ccns_annual_compensation,
    validate_ccns_monthly_compensation,
)
from application.control.contract_creation_rules_bridge import build_ccns_creation_rules_preflight
from application.control.contract_final_preflight import (
    ContractFinalPreflightDecision,
    ContractFinalPreflightService,
)
from domain.contracts.cee_compensation import legal_cee_daily_minimum
from domain.contracts.cee_contract_guardrails import CEEContractGuardrailService
from domain.convention.seniority_timeline import CCNSContractSeniorityTimelineService
from domain.convention.smic import SmicTerritory, create_smic_catalog_2026


def getRGB(winColor):
    b = winColor >> 16
    g = winColor >> 8 & 255
    r = winColor & 255
    return (r,g,b)


def _is_cee_type(DB, IDtype):
    if IDtype is None:
        return False
    DB.ExecuterReq("SELECT nom, nom_abrege FROM contrats_types WHERE IDtype=%d;" % int(IDtype))
    rows = DB.ResultatReq()
    if not rows:
        return False
    nom, nom_abrege = rows[0]
    abrege = (nom_abrege or "").strip().upper()
    texte = (nom or "").strip().lower()
    return abrege == "CEE" or "engagement educatif" in texte or "engagement éducatif" in texte


def _decimal_or_none(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _date_or_none(value):
    if value in (None, "", "2999-01-01"):
        return None
    if type(value) is datetime.date:
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _age_on(birth_date, reference_date):
    if birth_date is None:
        return None
    return reference_date.year - birth_date.year - int(
        (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day)
    )


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.parent = self.GetGrandParent()

        self.label_titre = wx.StaticText(self, -1, _(u"Fin de l'assistant de création de contrat"))

        txtIntro = u"""
        <FONT face="Arial" color="#000000" size=2>
        <P>Vous avez saisi toutes les données du contrat. Cliquez sur le bouton 'Valider' pour terminer l'assistant.</P>
        <p>Vous pouvez ensuite par exemple imprimer ce contrat ou la déclaration unique d'embauche correspondante.</p>
        </FONT>
        """
        self.label_intro = FonctionsPerso.TexteHtml(self, texte=txtIntro, Enabled=False)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 20)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)

    def _BuildCompensationPreflight(self, DB, dictContrats):
        reference_date = datetime.date.fromisoformat(dictContrats["date_debut"])
        is_cee = _is_cee_type(DB, dictContrats.get("IDtype"))

        if is_cee:
            qualification = dictContrats.get("cee_qualification")
            # Contrat historique antérieur à TW-184 : ne pas imposer de conversion.
            if not qualification and dictContrats.get("IDcontrat"):
                return ContractCompensationPreflight(
                    True,
                    "Contrat CEE historique conservé sans conversion forcée.",
                    control_scope="CEE_LEGACY",
                )
            legal = legal_cee_daily_minimum(
                smic_catalog=create_smic_catalog_2026(),
                reference_date=reference_date,
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
            rate = None
            if qualification:
                applicable = UTILS_CEE_baremes.GetApplicableRate(DB, qualification, reference_date)
                if applicable is not None:
                    rate = Decimal(str(applicable["montant_journalier"]))
            return validate_cee_daily_compensation(
                qualification=qualification,
                employer_daily_rate=rate,
                legal_minimum_daily_rate=legal,
            )

        if dictContrats.get("convention_code") == "CCNS":
            group = dictContrats.get("ccns_group")
            if not group:
                return ContractCompensationPreflight(
                    False,
                    "Le groupe CCNS est obligatoire pour ce contrat.",
                    control_scope="CCNS",
                )
            weekly = _decimal_or_none(dictContrats.get("weekly_hours")) or Decimal("0.00")
            monthly_salary = _decimal_or_none(dictContrats.get("gross_monthly_salary"))
            result = validate_ccns_monthly_compensation(
                group_code=group,
                reference_date=reference_date,
                weekly_hours=weekly,
                gross_monthly_salary=monthly_salary,
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
            if result.control_scope == "CCNS_ANNUAL":
                return validate_ccns_annual_compensation(
                    group_code=group,
                    reference_date=reference_date,
                    weekly_hours=weekly,
                    gross_annual_salary=_decimal_or_none(dictContrats.get("gross_annual_salary")),
                    reference_period_months=12,
                )
            return result

        return ContractCompensationPreflight(
            True,
            "Aucun contrôle de rémunération TW-184 applicable à ce contrat.",
            control_scope="OUTSIDE_SCOPE",
        )

    def _ExplicitPreviousContractMonths(self, DB, dictContrats, current_contract_start):
        previous_id = dictContrats.get("previous_contract_id")
        if not previous_id:
            return None
        person_id = int(dictContrats["IDpersonne"])
        months = 0
        seen = set()
        current_id = int(previous_id)
        expected_child_start = current_contract_start
        while current_id:
            if current_id in seen:
                raise ValueError("Boucle détectée dans la chaîne explicite des contrats précédents.")
            seen.add(current_id)
            DB.ExecuterReq(
                "SELECT IDpersonne, date_debut, date_fin, previous_contract_id "
                "FROM contrats WHERE IDcontrat=%d;" % current_id
            )
            rows = DB.ResultatReq()
            if not rows:
                raise ValueError("Le contrat précédent explicite est introuvable.")
            row_person_id, start_raw, end_raw, parent_id = rows[0]
            if int(row_person_id) != person_id:
                raise ValueError("La chaîne de contrats précédents contient un contrat d'une autre personne.")
            start = _date_or_none(start_raw)
            end = _date_or_none(end_raw)
            if start is None or end is None:
                raise ValueError("La chaîne explicite contient un contrat sans dates exploitables.")
            if end + datetime.timedelta(days=1) != expected_child_start:
                raise ValueError("La chaîne explicite des contrats n'est pas continue.")
            months += CCNSContractSeniorityTimelineService.completed_calendar_months(
                start,
                end + datetime.timedelta(days=1),
            )
            expected_child_start = start
            current_id = int(parent_id) if parent_id else 0
        return months

    def _HasUnlinkedPriorContracts(self, DB, dictContrats, start_date):
        person_id = int(dictContrats["IDpersonne"])
        current_id = int(dictContrats.get("IDcontrat") or 0)
        req = (
            "SELECT COUNT(*) FROM contrats WHERE IDpersonne=%d AND IDcontrat<>%d "
            "AND date_debut<'%s';"
            % (person_id, current_id, start_date.isoformat())
        )
        DB.ExecuterReq(req)
        rows = DB.ResultatReq()
        return bool(rows and int(rows[0][0] or 0) > 0)

    def _BuildCCNSRulesPreflight(self, DB, dictContrats, compensation):
        if dictContrats.get("convention_code") != "CCNS":
            return None
        group = dictContrats.get("ccns_group")
        weekly = _decimal_or_none(dictContrats.get("weekly_hours"))
        if not group or weekly is None or weekly <= Decimal("0.00"):
            return None

        start = datetime.date.fromisoformat(dictContrats["date_debut"])
        end = _date_or_none(dictContrats.get("date_fin"))
        evaluation_date = datetime.date.today()
        if evaluation_date < start:
            evaluation_date = start

        explicit_months = self._ExplicitPreviousContractMonths(DB, dictContrats, start)
        history_known_absent = False
        recognized_effective = None
        recognized_company = None
        if explicit_months is not None:
            recognized_effective = explicit_months
            recognized_company = explicit_months
        elif not self._HasUnlinkedPriorContracts(DB, dictContrats, start):
            history_known_absent = True

        return build_ccns_creation_rules_preflight(
            group_code=group,
            reference_date=start,
            current_contract_start=start,
            evaluation_date=evaluation_date,
            current_contract_end=end,
            weekly_hours=weekly,
            compensation=compensation,
            recognized_effective_work_months_at_start=recognized_effective,
            recognized_company_seniority_months_at_start=recognized_company,
            history_known_absent=history_known_absent,
        )

    def _BuildCEEGuardrails(self, DB, dictContrats, compensation):
        if not _is_cee_type(DB, dictContrats.get("IDtype")):
            return None
        if compensation.control_scope == "CEE_LEGACY":
            return None

        start = datetime.date.fromisoformat(dictContrats["date_debut"])
        birth_date = None
        person_id = dictContrats.get("IDpersonne")
        if person_id:
            DB.ExecuterReq("SELECT date_naiss FROM personnes WHERE IDpersonne=%d;" % int(person_id))
            rows = DB.ResultatReq()
            if rows:
                birth_date = _date_or_none(rows[0][0])
        age = _age_on(birth_date, start)

        # Les jours réellement travaillés et la moyenne tous contrats doivent
        # venir du planning/audit lorsqu'ils sont disponibles. Ne jamais déduire
        # ces valeurs des seules dates calendaires du contrat.
        days_rolling = dictContrats.get("cee_days_rolling_12_months")
        if days_rolling not in (None, ""):
            days_rolling = int(days_rolling)
        else:
            days_rolling = None
        average_6m = _decimal_or_none(dictContrats.get("cee_average_weekly_hours_6m"))
        max_daily = _decimal_or_none(dictContrats.get("cee_planned_max_daily_hours"))
        max_weekly = _decimal_or_none(dictContrats.get("cee_planned_max_weekly_hours"))

        return CEEContractGuardrailService().evaluate(
            days_rolling_12_months=days_rolling,
            average_weekly_hours_all_contracts_6m=average_6m,
            worker_age_years=age,
            planned_max_daily_hours=max_daily,
            planned_max_weekly_hours=max_weekly,
            # La moyenne 48 h relève du planning/audit global ; ne pas bloquer la
            # création si la projection six mois n'est pas encore disponible.
            require_average_hours_check=False,
            # Pour un mineur, en revanche, l'absence d'horaires planifiés impose
            # une revue avant de considérer le contrôle comme complet.
            require_minor_schedule_check=True,
        )

    def _RunFinalPreflight(self, DB, dictContrats):
        compensation = self._BuildCompensationPreflight(DB, dictContrats)
        ccns_rules = self._BuildCCNSRulesPreflight(DB, dictContrats, compensation)
        cee_guardrails = self._BuildCEEGuardrails(DB, dictContrats, compensation)
        result = ContractFinalPreflightService().evaluate(
            compensation=compensation,
            ccns_rules=ccns_rules,
            cee_guardrails=cee_guardrails,
        )

        if result.decision is ContractFinalPreflightDecision.BLOCKED:
            detail = "\n".join("• %s" % message for message in result.blocking_messages())
            wx.MessageBox(
                _(u"Le contrat ne peut pas être validé :\n%s") % detail,
                _(u"Contrôle final du contrat"),
                wx.OK | wx.ICON_ERROR,
                parent=self,
            )
            return False

        if result.decision is ContractFinalPreflightDecision.REVIEW:
            detail = "\n".join("• %s" % message for message in result.review_messages())
            answer = wx.MessageBox(
                _(u"Le contrôle final demande une revue :\n%s\n\nEnregistrer quand même ce contrat ?") % detail,
                _(u"Revue du contrat"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
                parent=self,
            )
            return answer == wx.YES
        return True

    def Validation(self):
        dictContrats = self.GetGrandParent().dictContrats
        dictChamps = self.GetGrandParent().dictChamps
        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractEngineColumns(DB)

        # Défense en profondeur : le résultat métier agrégé pilote la validation.
        try:
            if not self._RunFinalPreflight(DB, dictContrats):
                DB.Close()
                return False
        except Exception as err:
            DB.Close()
            wx.MessageBox(
                _(u"Le contrôle final du contrat n'a pas pu être exécuté :\n%s") % err,
                _(u"Contrôle du contrat"), wx.OK | wx.ICON_ERROR, parent=self,
            )
            return False

        listeDonnees = [
            ("IDpersonne", dictContrats["IDpersonne"]),
            ("IDclassification", dictContrats["IDclassification"]),
            ("IDtype", dictContrats["IDtype"]),
            ("valeur_point", dictContrats["valeur_point"]),
            ("cee_qualification", dictContrats.get("cee_qualification")),
            ("convention_code", dictContrats.get("convention_code")),
            ("ccns_group", dictContrats.get("ccns_group")),
            ("weekly_hours", dictContrats.get("weekly_hours")),
            ("gross_monthly_salary", dictContrats.get("gross_monthly_salary")),
            ("gross_annual_salary", dictContrats.get("gross_annual_salary")),
            ("operation_type", dictContrats.get("operation_type")),
            ("previous_contract_id", dictContrats.get("previous_contract_id")),
            ("trial_period_value", dictContrats.get("trial_period_value")),
            ("trial_period_unit", dictContrats.get("trial_period_unit")),
            ("date_debut", dictContrats["date_debut"]),
            ("date_fin", dictContrats["date_fin"]),
            ("date_rupture", dictContrats["date_rupture"]),
            ("essai", dictContrats["essai"]),
        ]

        if dictContrats["IDcontrat"] == 0:
            listeDonnees.append(("signature", ""))
            listeDonnees.append(("due", ""))
            IDcontrat = DB.ReqInsert("contrats", listeDonnees)
            DB.Commit()
        else:
            DB.ReqMAJ("contrats", listeDonnees, "IDcontrat", dictContrats["IDcontrat"])
            DB.Commit()
            IDcontrat = dictContrats["IDcontrat"]

        req = "SELECT IDval_champ, IDchamp FROM contrats_valchamps WHERE (IDcontrat=%d AND type='contrat')  ;" % IDcontrat
        DB.ExecuterReq(req)
        listeChampsDB = DB.ResultatReq()

        for IDchamp, valeur in dictChamps.items():
            donneesChamp = [
                ("IDchamp", IDchamp),
                ("type", "contrat"),
                ("valeur", valeur),
                ("IDcontrat", IDcontrat),
                ("IDmodele", 0),
            ]
            modif = False
            for IDval_champDB, IDchampDB in listeChampsDB:
                if IDchampDB == IDchamp:
                    DB.ReqMAJ("contrats_valchamps", donneesChamp, "IDval_champ", IDval_champDB)
                    DB.Commit()
                    modif = True
            if modif == False:
                DB.ReqInsert("contrats_valchamps", donneesChamp)
                DB.Commit()

        for IDval_champDB, IDchampDB in listeChampsDB:
            trouve = False
            for IDchamp, valeur in dictChamps.items():
                if IDchampDB == IDchamp:
                    trouve = True
            if trouve == False:
                DB.ReqDEL("contrats_valchamps", "IDval_champ", IDval_champDB)

        DB.Close()

        if FonctionsPerso.FrameOuverte("FicheIndividuelle") != None:
            self.GetGrandParent().GetParent().list_ctrl_contrats.Remplissage()
            self.GetGrandParent().GetParent().MAJ_barre_problemes()

        return True
