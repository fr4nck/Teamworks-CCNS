#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur:        Ivan LUCAS
# Copyright:    (c) 2008-09 Ivan LUCAS
# Licence:      Licence GNU GPL
#-----------------------------------------------------------

import datetime
from decimal import Decimal, InvalidOperation

import wx
from Utils.UTILS_Traduction import _
import GestionDB
import FonctionsPerso
from Dlg import DLG_Config_classifications
from Dlg import DLG_Config_val_point
from Dlg import DLG_Config_types_contrats
from Dlg import DLG_Config_cee_baremes
from Utils import UTILS_CEE_baremes

from application.control.ccns_contract_compliance import CCNSContractCompliancePresenter
from domain.contracts.cee_compensation import legal_cee_daily_minimum
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.smic import SmicTerritory, create_smic_catalog_2026

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED
else:
    from wx import DatePickerCtrl, DP_DROPDOWN
    EVT_DATE_CHANGED = wx.EVT_DATE_CHANGED


CEE_QUALIFICATIONS = (
    ("BAFA_HOLDER", u"BAFA titulaire"),
    ("BAFA_TRAINEE", u"BAFA stagiaire"),
    ("UNQUALIFIED", u"Non diplômé"),
    ("EQUIVALENT", u"Qualification équivalente"),
    ("BAFD_HOLDER", u"BAFD titulaire"),
    ("BAFD_TRAINEE", u"BAFD stagiaire"),
)

CONVENTIONS = (
    ("CCNS", u"CCNS — Sport (IDCC 2511)"),
    ("ECLAT", u"ÉCLAT"),
    ("CENTRES_SOCIAUX", u"Centres sociaux"),
    ("OTHER", u"Autre / hors moteur conventionnel"),
)


class Page(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)

        self.dictTypes = {}
        self.dictTypeCodes = {}
        self.ccns_presenter = CCNSContractCompliancePresenter()
        self.smic_catalog = create_smic_catalog_2026()
        self.ccns_choices = ()
        self.last_ccns_preview = None

        self.sizer_dates_staticbox = wx.StaticBox(self, -1, _(u"Dates du contrat"))
        self.sizer_caract_staticbox = wx.StaticBox(self, -1, _(u"Régime et caractéristiques"))
        self.sizer_ccns_staticbox = wx.StaticBox(self, -1, _(u"Contrôle CCNS / SMIC"))
        self.sizer_cee_staticbox = wx.StaticBox(self, -1, _(u"Barème CEE"))
        self.sizer_essai_staticbox = wx.StaticBox(self, -1, _(u"Période d'essai"))

        self.label_titre = wx.StaticText(self, -1, _(u"2. Caractéristiques générales du contrat"))
        self.label_intro = wx.StaticText(self, -1, _(u"Sélectionnez le régime applicable au contrat."))

        self.label_convention = wx.StaticText(self, -1, _(u"Convention applicable :"))
        self.choice_convention = wx.Choice(self, -1, choices=[])
        self._InitConventionChoice()
        self.convention_spacer = wx.StaticText(self, -1, "")

        self.label_type = wx.StaticText(self, -1, _(u"Type de contrat :"))
        self.choice_type = wx.Choice(self, -1, choices=[])
        self.Importation_Type()
        self.bouton_type = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        # Nouveau moteur CCNS : groupe conventionnel explicite.
        self.label_ccns_group = wx.StaticText(self, -1, _(u"Groupe CCNS :"))
        self.choice_ccns_group = wx.Choice(self, -1, choices=[])
        self.ccns_group_spacer = wx.StaticText(self, -1, "")

        # CEE : qualification/statut et non classification CCNS.
        self.label_cee_qualification = wx.StaticText(self, -1, _(u"Qualification / statut CEE :"))
        self.choice_cee_qualification = wx.Choice(self, -1, choices=[])
        for code, label in CEE_QUALIFICATIONS:
            self.choice_cee_qualification.Append(label, code)
        self.cee_qualification_spacer = wx.StaticText(self, -1, "")

        # Parcours historique conservé pour les contrats non modernisés.
        self.label_class = wx.StaticText(self, -1, _(u"Classification historique :"))
        self.choice_class = wx.Choice(self, -1, choices=[])
        self.Importation_classifications()
        self.bouton_class = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        self.label_valpoint = wx.StaticText(self, -1, _(u"Valeur du point historique :"))
        self.choice_valpoint = wx.Choice(self, -1, choices=[])
        self.Importation_valPoint()
        self.bouton_valpoint = wx.Button(self, -1, "...", style=wx.BU_EXACTFIT)

        # Données standardisées du contrat, réutilisables par les autres conventions.
        self.label_weekly_hours = wx.StaticText(self, -1, _(u"Durée hebdomadaire :"))
        self.weekly_hours = wx.SpinCtrlDouble(self, -1, min=0.0, max=80.0, initial=35.0, inc=0.25)
        self.weekly_hours.SetDigits(2)
        self.label_weekly_unit = wx.StaticText(self, -1, _(u"h / semaine"))

        self.label_monthly_salary = wx.StaticText(self, -1, _(u"Rémunération brute :"))
        self.monthly_salary = wx.TextCtrl(self, -1, "")
        self.label_monthly_unit = wx.StaticText(self, -1, _(u"€ brut / mois"))

        self.label_ccns_preview = wx.StaticText(self, -1, "")
        self.label_ccns_preview.Wrap(620)

        self.label_cee_preview = wx.StaticText(self, -1, "")
        self.label_cee_preview.Wrap(520)
        self.bouton_cee_baremes = wx.Button(self, -1, _(u"Barèmes CEE…"))

        self.label_date_debut = wx.StaticText(self, -1, _(u"À partir du :"))
        self.datepicker_date_debut = DatePickerCtrl(self, -1, style=DP_DROPDOWN)
        self.label_date_fin = wx.StaticText(self, -1, _(u"Jusqu'au :"))
        self.datepicker_date_fin = DatePickerCtrl(self, -1, style=DP_DROPDOWN)
        self.datepicker_date_debut.Enable(False)
        self.datepicker_date_fin.Enable(False)

        self.check_rupture = wx.CheckBox(self, -1, _(u"Rupture anticipée du contrat au :"))
        self.datepicker_rupture = DatePickerCtrl(self, -1, style=DP_DROPDOWN)
        self.datepicker_rupture.Enable(False)

        self.label_essai = wx.StaticText(self, -1, _(u"Nombre de jours :"))
        self.periode_essai = wx.SpinCtrl(self, -1, "", size=(70, -1))
        self.periode_essai.SetRange(0, 365)
        self.periode_essai.SetValue(0)
        self.aide_essai = wx.StaticText(
            self, -1,
            _(u"Règle historique : le moteur de période d'essai sera raccordé convention par convention."),
        )
        self.aide_essai.SetForegroundColour('Grey')

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonClassifications, self.bouton_class)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonValPoint, self.bouton_valpoint)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonType, self.bouton_type)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCEEBaremes, self.bouton_cee_baremes)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceType, self.choice_type)
        self.Bind(wx.EVT_CHOICE, self.OnChoiceConvention, self.choice_convention)
        self.Bind(wx.EVT_CHOICE, self.OnCCNSFieldChanged, self.choice_ccns_group)
        self.Bind(wx.EVT_CHOICE, self.OnCEEFieldChanged, self.choice_cee_qualification)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnCCNSFieldChanged, self.weekly_hours)
        self.Bind(wx.EVT_TEXT, self.OnCCNSFieldChanged, self.monthly_salary)
        self.Bind(EVT_DATE_CHANGED, self.OnContractDateChanged, self.datepicker_date_debut)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckRupture, self.check_rupture)

        self.Affichage_dateFin()
        if self.GetGrandParent().dictContrats["IDcontrat"] != 0:
            self.Importation()
        else:
            self._SelectConvention("CCNS")
        self.RefreshContractRules()

    def __set_properties(self):
        self.label_titre.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.bouton_type.SetMinSize((20, 20))
        self.bouton_type.SetToolTip(wx.ToolTip(_(u"Ajouter, modifier ou supprimer des types de contrat")))
        self.bouton_class.SetMinSize((20, 20))
        self.bouton_class.SetToolTip(wx.ToolTip(_(u"Configurer les classifications historiques")))
        self.bouton_valpoint.SetMinSize((20, 20))
        self.bouton_valpoint.SetToolTip(wx.ToolTip(_(u"Configurer les anciennes valeurs de point")))
        self.check_rupture.SetToolTip(wx.ToolTip(_(u"Saisir une date de rupture anticipée")))
        self.SetMinSize((690, 570))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=7, cols=1, vgap=8, hgap=8)
        grid_sizer_base.Add(self.label_titre, 0, 0, 0)
        grid_sizer_base.Add(self.label_intro, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        # Régime / type / classification contextuelle
        self.sizer_caract = wx.StaticBoxSizer(self.sizer_caract_staticbox, wx.VERTICAL)
        grid_caract = wx.FlexGridSizer(rows=6, cols=3, vgap=5, hgap=6)
        rows = (
            (self.label_convention, self.choice_convention, self.convention_spacer),
            (self.label_type, self.choice_type, self.bouton_type),
            (self.label_ccns_group, self.choice_ccns_group, self.ccns_group_spacer),
            (self.label_cee_qualification, self.choice_cee_qualification, self.cee_qualification_spacer),
            (self.label_class, self.choice_class, self.bouton_class),
            (self.label_valpoint, self.choice_valpoint, self.bouton_valpoint),
        )
        for label, control, extra in rows:
            grid_caract.Add(label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            grid_caract.Add(control, 0, wx.EXPAND)
            grid_caract.Add(extra, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_caract.AddGrowableCol(1)
        self.sizer_caract.Add(grid_caract, 1, wx.ALL | wx.EXPAND, 7)
        grid_sizer_base.Add(self.sizer_caract, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        # CCNS
        self.sizer_ccns = wx.StaticBoxSizer(self.sizer_ccns_staticbox, wx.VERTICAL)
        grid_ccns = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=6)
        grid_ccns.Add(self.label_weekly_hours, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_ccns.Add(self.weekly_hours, 0)
        grid_ccns.Add(self.label_weekly_unit, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_ccns.Add(self.label_monthly_salary, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_ccns.Add(self.monthly_salary, 0, wx.EXPAND)
        grid_ccns.Add(self.label_monthly_unit, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_ccns.AddGrowableCol(1)
        self.sizer_ccns.Add(grid_ccns, 0, wx.ALL | wx.EXPAND, 7)
        self.sizer_ccns.Add(self.label_ccns_preview, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 9)
        grid_sizer_base.Add(self.sizer_ccns, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        # CEE
        self.sizer_cee = wx.StaticBoxSizer(self.sizer_cee_staticbox, wx.VERTICAL)
        row_cee = wx.BoxSizer(wx.HORIZONTAL)
        row_cee.Add(self.label_cee_preview, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        row_cee.Add(self.bouton_cee_baremes, 0)
        self.sizer_cee.Add(row_cee, 0, wx.ALL | wx.EXPAND, 7)
        grid_sizer_base.Add(self.sizer_cee, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        # Dates
        sizer_dates = wx.StaticBoxSizer(self.sizer_dates_staticbox, wx.VERTICAL)
        grid_dates = wx.FlexGridSizer(rows=2, cols=4, vgap=5, hgap=6)
        grid_dates.Add(self.label_date_debut, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_dates.Add(self.datepicker_date_debut, 0)
        grid_dates.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_dates.Add(self.datepicker_date_fin, 0)
        grid_dates.Add((1, 1), 0)
        grid_dates.Add(self.check_rupture, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_dates.Add((1, 1), 0)
        grid_dates.Add(self.datepicker_rupture, 0)
        sizer_dates.Add(grid_dates, 0, wx.ALL | wx.EXPAND, 7)
        grid_sizer_base.Add(sizer_dates, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        # Essai
        self.sizer_essai = wx.StaticBoxSizer(self.sizer_essai_staticbox, wx.VERTICAL)
        row_essai = wx.BoxSizer(wx.HORIZONTAL)
        row_essai.Add(self.label_essai, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row_essai.Add(self.periode_essai, 0, wx.RIGHT, 8)
        row_essai.Add(self.aide_essai, 1, wx.ALIGN_CENTER_VERTICAL)
        self.sizer_essai.Add(row_essai, 0, wx.ALL | wx.EXPAND, 7)
        grid_sizer_base.Add(self.sizer_essai, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 20)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)

    def _InitConventionChoice(self):
        self.choice_convention.Clear()
        if self.GetGrandParent().dictContrats.get("IDcontrat") and not self.GetGrandParent().dictContrats.get("convention_code"):
            self.choice_convention.Append(_(u"Non renseignée (contrat historique)"), None)
        for code, label in CONVENTIONS:
            self.choice_convention.Append(label, code)

    def _SelectConvention(self, code):
        for index in range(self.choice_convention.GetCount()):
            if self.choice_convention.GetClientData(index) == code:
                self.choice_convention.SetSelection(index)
                return

    def Importation(self):
        data = self.GetGrandParent().dictContrats
        IDtype = data["IDtype"]
        self.SelectChoice(self.choice_type, IDtype)
        self.SelectChoice(self.choice_class, data.get("IDclassification"))
        self.SelectChoice(self.choice_valpoint, data.get("valeur_point"))
        self.SelectChoice(self.choice_cee_qualification, data.get("cee_qualification"))
        self._SelectConvention(data.get("convention_code"))

        if data.get("weekly_hours") not in (None, ""):
            try:
                self.weekly_hours.SetValue(float(data["weekly_hours"]))
            except (TypeError, ValueError):
                pass
        if data.get("gross_monthly_salary") not in (None, ""):
            self.monthly_salary.SetValue(str(data["gross_monthly_salary"]).replace(".", ","))

        if data["date_rupture"] != "":
            self.check_rupture.SetValue(True)
            self.datepicker_rupture.Enable(True)
            self.SetDatePicker(self.datepicker_rupture, data["date_rupture"])
        else:
            self.check_rupture.SetValue(False)
            self.datepicker_rupture.Enable(False)

        date_debut = data["date_debut"]
        date_fin = data["date_fin"]
        if date_debut != "":
            self.SetDatePicker(self.datepicker_date_debut, date_debut)
        if date_fin != "" and date_fin != "2999-01-01":
            self.SetDatePicker(self.datepicker_date_fin, date_fin)
        self.datepicker_date_debut.Enable(True)
        self.datepicker_date_fin.Enable(True)
        self.Affichage_dateFin()
        self.periode_essai.SetValue(data["essai"] or 0)
        self.RefreshCCNSGroups(preserve=data.get("ccns_group"))

    def CalcEssai(self):
        selection = self.choice_type.GetSelection()
        if selection == -1 or self.IsCEESelected():
            return
        IDtype = self.choice_type.GetClientData(selection)
        if self.dictTypes.get(IDtype) == "oui" and self.GetGrandParent().dictContrats.get("IDcontrat") == 0:
            self.periode_essai.SetValue(30)

    def SetDatePicker(self, controle, date):
        annee = int(date[:4])
        mois = int(date[5:7]) - 1
        jour = int(date[8:10])
        valeur = wx.DateTime()
        valeur.Set(jour, mois, annee)
        controle.SetValue(valeur)

    def GetDatePickerValue(self, controle):
        value = controle.GetValue()
        return str(datetime.date(value.GetYear(), value.GetMonth() + 1, value.GetDay()))

    def GetReferenceDate(self):
        value = self.datepicker_date_debut.GetValue()
        return datetime.date(value.GetYear(), value.GetMonth() + 1, value.GetDay())

    def GetChoiceData(self, controle):
        selection = controle.GetSelection()
        if selection != -1:
            return controle.GetClientData(selection)
        return None

    def SelectChoice(self, controle, data):
        if data is None:
            return
        for index in range(controle.GetCount()):
            if controle.GetClientData(index) == data:
                controle.SetSelection(index)
                return

    def _GetContractTypeCode(self, nom, nom_abrege):
        abrege = (nom_abrege or "").strip().upper()
        texte = (nom or "").strip().lower()
        if abrege == "CEE" or "engagement educatif" in texte or "engagement éducatif" in texte:
            return "CEE"
        return abrege

    def IsCEESelected(self):
        selection = self.choice_type.GetSelection()
        if selection == -1:
            return False
        IDtype = self.choice_type.GetClientData(selection)
        return self.dictTypeCodes.get(IDtype) == "CEE"

    def IsCCNSSelected(self):
        return self.GetChoiceData(self.choice_convention) == "CCNS" and not self.IsCEESelected()

    def IsLegacyCEEWithoutQualification(self):
        data = self.GetGrandParent().dictContrats
        if not data.get("IDcontrat"):
            return False
        original_type = data.get("IDtype")
        return self.dictTypeCodes.get(original_type) == "CEE" and data.get("cee_qualification") in (None, "")

    def IsLegacyGenericPath(self):
        convention = self.GetChoiceData(self.choice_convention)
        return not self.IsCEESelected() and convention != "CCNS"

    def RefreshContractRules(self):
        is_cee = self.IsCEESelected()
        is_ccns = self.IsCCNSSelected()
        legacy = self.IsLegacyGenericPath()

        for control in (self.label_ccns_group, self.choice_ccns_group, self.ccns_group_spacer):
            control.Show(is_ccns)
        for control in (self.label_cee_qualification, self.choice_cee_qualification, self.cee_qualification_spacer):
            control.Show(is_cee)
        for control in (self.label_class, self.choice_class, self.bouton_class,
                        self.label_valpoint, self.choice_valpoint, self.bouton_valpoint):
            control.Show(legacy)

        self._ShowStaticSizer(self.sizer_ccns, is_ccns)
        self._ShowStaticSizer(self.sizer_cee, is_cee)
        self._ShowStaticSizer(self.sizer_essai, not is_cee)

        if is_cee and self.IsLegacyCEEWithoutQualification():
            self.label_intro.SetLabel(_(u"CEE historique : les anciennes données restent conservées. Choisissez une qualification pour passer au moteur de barème CEE."))
        elif is_cee:
            self.label_intro.SetLabel(_(u"CEE : la qualification détermine le barème employeur ; aucune classification CCNS n'est utilisée."))
        elif is_ccns:
            self.label_intro.SetLabel(_(u"CCNS : choisissez le groupe, puis Teamworks compare automatiquement le minimum conventionnel au SMIC applicable."))
        elif self.GetChoiceData(self.choice_convention) in ("ECLAT", "CENTRES_SOCIAUX"):
            self.label_intro.SetLabel(_(u"Convention reconnue, moteur détaillé pas encore raccordé : le parcours historique est conservé sans prétendre à un contrôle conventionnel."))
        else:
            self.label_intro.SetLabel(_(u"Contrat historique ou hors moteur conventionnel."))

        if is_ccns:
            self.RefreshCCNSGroups(preserve=self.GetChoiceData(self.choice_ccns_group))
            self.RefreshCCNSPreview()
        if is_cee:
            self.RefreshCEEPreview()
        self.Layout()
        if self.GetParent():
            self.GetParent().Layout()

    @staticmethod
    def _ShowStaticSizer(sizer, show):
        sizer.GetStaticBox().Show(show)
        sizer.ShowItems(show)

    def RefreshCCNSGroups(self, preserve=None):
        if not self.IsCCNSSelected():
            return
        try:
            choices = self.ccns_presenter.group_choices(self.GetReferenceDate())
        except Exception as err:
            self.ccns_choices = ()
            self.choice_ccns_group.Clear()
            self.label_ccns_preview.SetLabel(_(u"Grille CCNS indisponible pour cette date : %s") % err)
            return
        self.ccns_choices = choices
        self.choice_ccns_group.Clear()
        for item in choices:
            if item.periodicity is SalaryMinimumPeriodicity.ANNUAL:
                label = u"%s — minimum annuel %s €" % (item.label, self._Money(item.minimum_amount))
            else:
                label = u"%s — minimum mensuel %s €" % (item.label, self._Money(item.minimum_amount))
            self.choice_ccns_group.Append(label, item.code)
        if preserve:
            self.SelectChoice(self.choice_ccns_group, preserve)

    @staticmethod
    def _Money(value):
        return ("%.2f" % Decimal(value)).replace(".", ",")

    def _MonthlySalaryDecimal(self):
        text = self.monthly_salary.GetValue().strip().replace(" ", "").replace(",", ".")
        if not text:
            return None
        try:
            value = Decimal(text)
        except InvalidOperation:
            return None
        if value < Decimal("0"):
            return None
        return value.quantize(Decimal("0.01"))

    def RefreshCCNSPreview(self):
        self.last_ccns_preview = None
        if not self.IsCCNSSelected():
            return
        group_code = self.GetChoiceData(self.choice_ccns_group)
        if not group_code:
            self.label_ccns_preview.SetLabel(_(u"Choisissez un groupe CCNS pour afficher le minimum applicable."))
            return
        choice = next((item for item in self.ccns_choices if item.code == group_code), None)
        if choice is None:
            self.label_ccns_preview.SetLabel(_(u"Groupe CCNS indisponible pour cette date."))
            return
        if choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
            self.label_monthly_salary.SetLabel(_(u"Rémunération brute :"))
            self.label_monthly_unit.SetLabel(_(u"€ brut / mois (informatif)"))
            self.label_ccns_preview.SetLabel(
                _(u"%s : minimum CCNS annuel %s €. Le contrôle automatique mensuel n'est volontairement pas utilisé pour G7/G8.")
                % (choice.label, self._Money(choice.minimum_amount))
            )
            return

        self.label_monthly_salary.SetLabel(_(u"Rémunération brute :"))
        self.label_monthly_unit.SetLabel(_(u"€ brut / mois"))
        salary = self._MonthlySalaryDecimal()
        remuneration = salary if salary is not None else Decimal("0.00")
        try:
            preview = self.ccns_presenter.evaluate_monthly(
                group_code=group_code,
                reference_date=self.GetReferenceDate(),
                weekly_hours=Decimal(str(self.weekly_hours.GetValue())),
                remuneration_amount=remuneration,
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
        except Exception as err:
            self.label_ccns_preview.SetLabel(_(u"Contrôle CCNS indisponible : %s") % err)
            return
        self.last_ccns_preview = preview
        source = {"ccns": "CCNS", "smic": "SMIC", "equal": "CCNS = SMIC"}.get(preview.source, preview.source)
        if salary is None:
            status = _(u"saisissez la rémunération pour contrôler la conformité")
        elif preview.compliant:
            status = _(u"CONFORME")
        else:
            status = _(u"NON CONFORME — manque %s €") % self._Money(-preview.difference_amount)
        self.label_ccns_preview.SetLabel(
            _(u"Minimum CCNS : %s € | SMIC : %s € | Minimum retenu : %s € (%s) | %s")
            % (
                self._Money(preview.ccns_minimum_amount),
                self._Money(preview.smic_minimum_amount),
                self._Money(preview.required_minimum_amount),
                source,
                status,
            )
        )

    def RefreshCEEPreview(self):
        if not self.IsCEESelected():
            return
        qualification = self.GetChoiceData(self.choice_cee_qualification)
        if not qualification:
            if self.IsLegacyCEEWithoutQualification():
                self.label_cee_preview.SetLabel(_(u"CEE historique : aucun statut moderne enregistré."))
            else:
                self.label_cee_preview.SetLabel(_(u"Choisissez la qualification CEE pour afficher le barème."))
            return
        try:
            legal = legal_cee_daily_minimum(
                smic_catalog=self.smic_catalog,
                reference_date=self.GetReferenceDate(),
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
            DB = GestionDB.DB()
            try:
                rate = UTILS_CEE_baremes.GetApplicableRate(DB, qualification, self.GetReferenceDate())
            finally:
                DB.Close()
        except Exception as err:
            self.label_cee_preview.SetLabel(_(u"Barème CEE indisponible : %s") % err)
            return
        if rate is None:
            self.label_cee_preview.SetLabel(
                _(u"Aucun barème employeur configuré. Minimum légal à cette date : %s € brut/jour.")
                % self._Money(legal)
            )
            return
        employer = Decimal(rate["montant_journalier"])
        if employer >= legal:
            status = _(u"CONFORME")
        else:
            status = _(u"NON CONFORME")
        self.label_cee_preview.SetLabel(
            _(u"Barème employeur : %s € brut/jour | Minimum légal : %s € | %s")
            % (self._Money(employer), self._Money(legal), status)
        )

    def OnChoiceConvention(self, event):
        self.RefreshContractRules()

    def OnChoiceType(self, event):
        self.datepicker_date_debut.Enable(True)
        self.datepicker_date_fin.Enable(True)
        self.Affichage_dateFin()
        self.CalcEssai()
        self.RefreshContractRules()

    def OnCCNSFieldChanged(self, event):
        self.RefreshCCNSPreview()
        if event:
            event.Skip()

    def OnCEEFieldChanged(self, event):
        self.RefreshCEEPreview()
        if event:
            event.Skip()

    def OnContractDateChanged(self, event):
        selected_group = self.GetChoiceData(self.choice_ccns_group)
        if self.IsCCNSSelected():
            self.RefreshCCNSGroups(preserve=selected_group)
            self.RefreshCCNSPreview()
        if self.IsCEESelected():
            self.RefreshCEEPreview()
        if event:
            event.Skip()

    def OnCheckRupture(self, event):
        self.datepicker_rupture.Enable(self.check_rupture.GetValue())

    def Affichage_dateFin(self):
        selection = self.choice_type.GetSelection()
        if selection == -1:
            return
        IDselection = self.choice_type.GetClientData(selection)
        if self.dictTypes.get(IDselection) == "non":
            self.label_date_fin.Show(True)
            self.datepicker_date_fin.Show(True)
        else:
            self.label_date_fin.Show(False)
            self.datepicker_date_fin.Show(False)

    def OnBoutonCEEBaremes(self, event):
        dlg = DLG_Config_cee_baremes.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.RefreshCEEPreview()

    def OnBoutonClassifications(self, event):
        dlg = DLG_Config_classifications.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.Importation_classifications()

    def OnBoutonValPoint(self, event):
        dlg = DLG_Config_val_point.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.Importation_valPoint()

    def OnBoutonType(self, event):
        dlg = DLG_Config_types_contrats.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.Importation_Type()
        self.RefreshContractRules()

    def Importation_classifications(self):
        controle = self.choice_class
        selected = self.GetChoiceData(controle) if hasattr(self, "choice_class") else None
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM contrats_class ")
        rows = DB.ResultatReq()
        DB.Close()
        controle.Clear()
        for key, valeur in rows:
            controle.Append(valeur, key)
        self.SelectChoice(controle, selected)

    def Importation_valPoint(self):
        controle = self.choice_valpoint
        selected = self.GetChoiceData(controle) if hasattr(self, "choice_valpoint") else None
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM valeurs_point ORDER BY date_debut ")
        rows = DB.ResultatReq()
        DB.Close()
        dateJour = str(datetime.date.today())
        current = None
        for ID, valeur, dateDebut in rows:
            if dateJour >= dateDebut:
                current = ID
        controle.Clear()
        for ID, valeur, dateDebut in rows:
            txt = str(valeur) + _(u" €  (à partir du ") + FonctionsPerso.DateEngFr(dateDebut) + ")"
            controle.Append(txt, ID)
        self.SelectChoice(controle, selected if selected is not None else current)
        self.listeValPoint = rows

    def Importation_Type(self):
        controle = self.choice_type
        selected = self.GetChoiceData(controle) if hasattr(self, "choice_type") else None
        DB = GestionDB.DB()
        DB.ExecuterReq("SELECT * FROM contrats_types ")
        rows = DB.ResultatReq()
        DB.Close()
        controle.Clear()
        self.dictTypes = {}
        self.dictTypeCodes = {}
        for key, nom, nom_abrege, duree_indeterminee in rows:
            self.dictTypes[key] = duree_indeterminee
            self.dictTypeCodes[key] = self._GetContractTypeCode(nom, nom_abrege)
            controle.Append(nom, key)
        self.SelectChoice(controle, selected)

    def _ValidateLegacyPoint(self, date_debut, valPoint):
        valeurNecessaire = None
        for ID, valeur, dateValeur in self.listeValPoint:
            if date_debut >= dateValeur:
                valeurNecessaire = ID
        if valeurNecessaire is None:
            wx.MessageBox(
                _(u"Aucune valeur de point historique ne correspond à la date de début du contrat."),
                _(u"Valeur du point"), wx.OK | wx.ICON_ERROR, parent=self,
            )
            return False
        if valeurNecessaire != valPoint:
            wx.MessageBox(
                _(u"La valeur du point historique sélectionnée ne correspond pas à la date de début."),
                _(u"Valeur du point"), wx.OK | wx.ICON_ERROR, parent=self,
            )
            return False
        return True

    def Validation(self):
        IDtype = self.GetChoiceData(self.choice_type)
        convention = self.GetChoiceData(self.choice_convention)
        classification = self.GetChoiceData(self.choice_class)
        valPoint = self.GetChoiceData(self.choice_valpoint)
        cee_qualification = self.GetChoiceData(self.choice_cee_qualification)
        ccns_group = self.GetChoiceData(self.choice_ccns_group)
        date_debut = self.GetDatePickerValue(self.datepicker_date_debut)
        date_fin = self.GetDatePickerValue(self.datepicker_date_fin)
        rupture = self.check_rupture.GetValue()
        date_rupture = self.GetDatePickerValue(self.datepicker_rupture)
        essai = self.periode_essai.GetValue()

        if IDtype is None:
            wx.MessageBox(_(u"Vous devez sélectionner un type de contrat."), _(u"Contrat"), wx.OK | wx.ICON_ERROR, parent=self)
            self.choice_type.SetFocus()
            return False

        is_cee = self.IsCEESelected()
        is_ccns = self.IsCCNSSelected()
        legacy = self.IsLegacyGenericPath()

        weekly_hours = None
        gross_monthly_salary = None

        if is_cee:
            if cee_qualification is None and not self.IsLegacyCEEWithoutQualification():
                wx.MessageBox(
                    _(u"Vous devez sélectionner la qualification ou le statut CEE."),
                    _(u"CEE"), wx.OK | wx.ICON_ERROR, parent=self,
                )
                self.choice_cee_qualification.SetFocus()
                return False
            if cee_qualification is not None:
                classification = None
                valPoint = None
            ccns_group = None
            essai = 0
        elif is_ccns:
            if ccns_group is None:
                wx.MessageBox(_(u"Vous devez sélectionner le groupe CCNS."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                self.choice_ccns_group.SetFocus()
                return False
            weekly_hours = Decimal(str(self.weekly_hours.GetValue())).quantize(Decimal("0.01"))
            if weekly_hours <= 0:
                wx.MessageBox(_(u"La durée hebdomadaire doit être supérieure à zéro."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            choice = next((item for item in self.ccns_choices if item.code == ccns_group), None)
            if choice is None:
                wx.MessageBox(_(u"Le groupe CCNS sélectionné n'est pas applicable à cette date."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            salary = self._MonthlySalaryDecimal()
            if choice.periodicity is SalaryMinimumPeriodicity.MONTHLY:
                if salary is None or salary <= Decimal("0"):
                    wx.MessageBox(_(u"Vous devez saisir la rémunération brute mensuelle."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                    self.monthly_salary.SetFocus()
                    return False
                gross_monthly_salary = salary
                self.RefreshCCNSPreview()
                if self.last_ccns_preview is None:
                    wx.MessageBox(_(u"Le contrôle CCNS/SMIC n'a pas pu être calculé."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                    return False
                if not self.last_ccns_preview.compliant:
                    wx.MessageBox(
                        _(u"La rémunération saisie est inférieure au minimum CCNS/SMIC applicable. Corrigez le montant avant d'enregistrer le contrat."),
                        _(u"Rémunération non conforme"), wx.OK | wx.ICON_ERROR, parent=self,
                    )
                    self.monthly_salary.SetFocus()
                    return False
            else:
                gross_monthly_salary = salary
            classification = None
            valPoint = None
        elif legacy:
            if classification is None:
                wx.MessageBox(_(u"Vous devez sélectionner une classification historique."), _(u"Contrat"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            if valPoint is None:
                wx.MessageBox(_(u"Vous devez sélectionner une valeur de point historique."), _(u"Contrat"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            if not self._ValidateLegacyPoint(date_debut, valPoint):
                return False

        if date_debut > date_fin and self.datepicker_date_fin.IsShown():
            wx.MessageBox(_(u"La date de fin est antérieure à la date de début."), _(u"Dates"), wx.OK | wx.ICON_ERROR, parent=self)
            return False
        if rupture and date_debut > date_rupture:
            wx.MessageBox(_(u"La date de rupture est antérieure à la date de début."), _(u"Dates"), wx.OK | wx.ICON_ERROR, parent=self)
            return False
        if rupture and self.datepicker_date_fin.IsShown() and date_rupture >= date_fin:
            wx.MessageBox(_(u"La date de rupture doit être antérieure à la date de fin."), _(u"Dates"), wx.OK | wx.ICON_ERROR, parent=self)
            return False

        if not is_cee and essai == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Aucune période d'essai n'est définie. Continuer quand même ?"),
                _(u"Période d'essai"),
                wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT,
            )
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_YES:
                return False

        data = self.GetGrandParent().dictContrats
        data["IDtype"] = IDtype
        data["IDclassification"] = classification
        data["valeur_point"] = valPoint
        data["cee_qualification"] = cee_qualification if is_cee else None
        data["convention_code"] = convention
        data["ccns_group"] = ccns_group if is_ccns else None
        data["weekly_hours"] = float(weekly_hours) if weekly_hours is not None else None
        data["gross_monthly_salary"] = float(gross_monthly_salary) if gross_monthly_salary is not None else None
        data["date_debut"] = date_debut
        data["date_fin"] = date_fin if self.datepicker_date_fin.IsShown() else "2999-01-01"
        data["date_rupture"] = date_rupture if rupture else ""
        data["essai"] = essai
        return True
