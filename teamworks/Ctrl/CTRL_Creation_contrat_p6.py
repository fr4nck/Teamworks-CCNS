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
    validate_cee_daily_compensation,
    validate_ccns_monthly_compensation,
)
from domain.contracts.cee_compensation import legal_cee_daily_minimum
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

    def _PreflightCompensation(self, DB, dictContrats):
        reference_date = datetime.date.fromisoformat(dictContrats["date_debut"])
        is_cee = _is_cee_type(DB, dictContrats.get("IDtype"))

        if is_cee:
            qualification = dictContrats.get("cee_qualification")
            # Contrat historique antérieur à TW-184 : ne pas imposer de conversion.
            if not qualification and dictContrats.get("IDcontrat"):
                return True
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
            result = validate_cee_daily_compensation(
                qualification=qualification,
                employer_daily_rate=rate,
                legal_minimum_daily_rate=legal,
            )
            if not result.compliant:
                detail = result.message
                if result.required_minimum is not None:
                    detail += _(u"\nMinimum requis : %.2f € brut/jour.") % result.required_minimum
                if result.proposed_amount is not None:
                    detail += _(u"\nBarème proposé : %.2f € brut/jour.") % result.proposed_amount
                wx.MessageBox(detail, _(u"Contrôle CEE"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            return True

        if dictContrats.get("convention_code") == "CCNS":
            group = dictContrats.get("ccns_group")
            if not group:
                wx.MessageBox(
                    _(u"Le groupe CCNS est obligatoire pour ce contrat."),
                    _(u"Contrôle CCNS"), wx.OK | wx.ICON_ERROR, parent=self,
                )
                return False
            weekly = _decimal_or_none(dictContrats.get("weekly_hours"))
            if weekly is None:
                weekly = Decimal("0.00")
            monthly_salary = _decimal_or_none(dictContrats.get("gross_monthly_salary"))
            result = validate_ccns_monthly_compensation(
                group_code=group,
                reference_date=reference_date,
                weekly_hours=weekly,
                gross_monthly_salary=monthly_salary,
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )

            if result.control_scope == "CCNS_ANNUAL":
                annual_salary = _decimal_or_none(dictContrats.get("gross_annual_salary"))
                if annual_salary is None or annual_salary <= Decimal("0"):
                    wx.MessageBox(
                        _(u"La rémunération brute annuelle est obligatoire pour les groupes G7/G8."),
                        _(u"Contrôle CCNS annuel"), wx.OK | wx.ICON_ERROR, parent=self,
                    )
                    return False
                # Le moteur annuel de temps partiel sera raccordé séparément.
                # À temps plein, le contrôle est déterministe et peut bloquer.
                if weekly == Decimal("35") and result.required_minimum is not None and annual_salary < result.required_minimum:
                    wx.MessageBox(
                        _(u"La rémunération annuelle est inférieure au minimum CCNS applicable.\nMinimum requis : %.2f € brut/an.")
                        % result.required_minimum,
                        _(u"Contrôle CCNS annuel"), wx.OK | wx.ICON_ERROR, parent=self,
                    )
                    return False
                return True

            if not result.compliant:
                detail = result.message
                if result.required_minimum is not None:
                    detail += _(u"\nMinimum requis : %.2f € brut/mois.") % result.required_minimum
                if result.proposed_amount is not None:
                    detail += _(u"\nRémunération proposée : %.2f € brut/mois.") % result.proposed_amount
                wx.MessageBox(detail, _(u"Contrôle CCNS / SMIC"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
        return True

    def Validation(self):
        dictContrats = self.GetGrandParent().dictContrats
        dictChamps = self.GetGrandParent().dictChamps
        DB = GestionDB.DB()
        UTILS_Contrats_schema.EnsureContractEngineColumns(DB)

        # Défense en profondeur : aucun contrat moderne incohérent n'est écrit.
        try:
            if not self._PreflightCompensation(DB, dictContrats):
                DB.Close()
                return False
        except Exception as err:
            DB.Close()
            wx.MessageBox(
                _(u"Le contrôle final de rémunération n'a pas pu être exécuté :\n%s") % err,
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
