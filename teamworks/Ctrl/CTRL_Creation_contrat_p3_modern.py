#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import datetime
from decimal import Decimal

import wx
import GestionDB
from Utils.UTILS_Traduction import _

from Ctrl.CTRL_Creation_contrat_p3 import Page as LegacyPage
from domain.contracts.contract_operation import ContractOperation
from domain.contracts.contract_type import ContractType
from domain.contracts.probation_period import (
    ProbationUnit,
    probation_calendar_days,
    propose_ccns_probation_period,
)
from domain.convention.salary_grid_entry import SalaryMinimumPeriodicity
from domain.convention.smic import SmicTerritory


OPERATION_CHOICES = (
    (ContractOperation.NEW, u"Nouveau contrat"),
    (ContractOperation.CDD_RENEWAL, u"Renouvellement d'un CDD"),
    (ContractOperation.CDD_TO_CDI, u"Passage CDD → CDI"),
)

TRIAL_UNIT_LABELS = (
    (ProbationUnit.DAY, u"jour(s) calendaires"),
    (ProbationUnit.MONTH, u"mois calendaires"),
)


class Page(LegacyPage):
    """Adaptateur métier TW-184 au-dessus de la page contrat historique."""

    def __init__(self, *args, **kwargs):
        self._modern_ready = False
        self._salary_prefill_guard = False
        self._auto_salary_value = None
        self._trial_user_modified = False
        self._previous_contracts = {}
        super().__init__(*args, **kwargs)

        self._BuildOperationControls()
        self._BuildTrialControls()
        self._LoadPreviousContracts()
        self._LoadModernState()
        self._modern_ready = True
        self._RefreshOperationVisibility()
        self.RefreshCCNSPreview()
        self.RefreshTrialProposal(force=not bool(self.GetGrandParent().dictContrats.get("IDcontrat")))
        self.Layout()

    # ------------------------------------------------------------------
    # Nature de l'opération et contrat précédent

    def _BuildOperationControls(self):
        self.label_operation = wx.StaticText(self, -1, _(u"Nature de l'opération :"))
        self.choice_operation = wx.Choice(self, -1, choices=[])
        data = self.GetGrandParent().dictContrats
        if data.get("IDcontrat") and not data.get("operation_type"):
            self.choice_operation.Append(_(u"Non renseignée (contrat historique)"), None)
        for operation, label in OPERATION_CHOICES:
            self.choice_operation.Append(_(label), operation.value)

        self.label_previous_contract = wx.StaticText(self, -1, _(u"Contrat précédent :"))
        self.choice_previous_contract = wx.Choice(self, -1, choices=[])
        self.previous_contract_hint = wx.StaticText(
            self, -1,
            _(u"Le contrat précédent permet de contrôler la continuité et de calculer la période d'essai restante."),
        )
        self.previous_contract_hint.SetForegroundColour("Grey")

        grid = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=6)
        grid.Add(self.label_operation, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.choice_operation, 0, wx.EXPAND)
        grid.Add((1, 1), 0)
        grid.Add(self.label_previous_contract, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.choice_previous_contract, 0, wx.EXPAND)
        grid.Add(self.previous_contract_hint, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.AddGrowableCol(1)
        self.sizer_caract.Insert(0, grid, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 7)

        self.Bind(wx.EVT_CHOICE, self.OnOperationChanged, self.choice_operation)
        self.Bind(wx.EVT_CHOICE, self.OnPreviousContractChanged, self.choice_previous_contract)

    def _LoadModernState(self):
        data = self.GetGrandParent().dictContrats
        operation = data.get("operation_type")
        if operation:
            self.SelectChoice(self.choice_operation, operation)
        elif data.get("IDcontrat"):
            if self.choice_operation.GetCount():
                self.choice_operation.SetSelection(0)
        else:
            self.SelectChoice(self.choice_operation, ContractOperation.NEW.value)

        previous_id = data.get("previous_contract_id")
        if previous_id:
            self.SelectChoice(self.choice_previous_contract, previous_id)

    def _LoadPreviousContracts(self):
        selected = self.GetChoiceData(self.choice_previous_contract) if self.choice_previous_contract.GetCount() else None
        self.choice_previous_contract.Clear()
        self._previous_contracts = {}
        person_id = self.GetGrandParent().dictContrats.get("IDpersonne")
        current_id = self.GetGrandParent().dictContrats.get("IDcontrat") or 0
        if not person_id:
            return

        DB = GestionDB.DB()
        try:
            req = (
                "SELECT c.IDcontrat, c.date_debut, c.date_fin, t.nom, t.nom_abrege "
                "FROM contrats c LEFT JOIN contrats_types t ON c.IDtype=t.IDtype "
                "WHERE c.IDpersonne=%d AND c.IDcontrat<>%d "
                "ORDER BY c.date_fin DESC, c.date_debut DESC;"
                % (int(person_id), int(current_id))
            )
            DB.ExecuterReq(req)
            rows = DB.ResultatReq()
        finally:
            DB.Close()

        for contract_id, date_start, date_end, type_name, type_short in rows:
            if self._GetContractTypeCode(type_name, type_short) != "CDD":
                continue
            if not date_start or not date_end or date_end == "2999-01-01":
                continue
            try:
                start = datetime.date.fromisoformat(str(date_start))
                end = datetime.date.fromisoformat(str(date_end))
            except (TypeError, ValueError):
                continue
            label = _(u"CDD du %s au %s") % (
                start.strftime("%d/%m/%Y"),
                end.strftime("%d/%m/%Y"),
            )
            self.choice_previous_contract.Append(label, int(contract_id))
            self._previous_contracts[int(contract_id)] = (start, end)

        if selected:
            self.SelectChoice(self.choice_previous_contract, selected)
        if self.choice_previous_contract.GetSelection() == -1 and self.choice_previous_contract.GetCount():
            self.choice_previous_contract.SetSelection(0)

    def _GetOperation(self):
        value = self.GetChoiceData(self.choice_operation)
        if not value:
            return None
        try:
            return ContractOperation(value)
        except ValueError:
            return None

    def _RefreshOperationVisibility(self):
        operation = self._GetOperation()
        show_previous = operation in (ContractOperation.CDD_RENEWAL, ContractOperation.CDD_TO_CDI)
        for control in (self.label_previous_contract, self.choice_previous_contract, self.previous_contract_hint):
            control.Show(show_previous)
        self.Layout()

    def _SelectContractTypeCode(self, code):
        for index in range(self.choice_type.GetCount()):
            type_id = self.choice_type.GetClientData(index)
            if self.dictTypeCodes.get(type_id) == code:
                self.choice_type.SetSelection(index)
                self.Affichage_dateFin()
                return True
        return False

    def OnOperationChanged(self, event):
        operation = self._GetOperation()
        if operation is ContractOperation.CDD_RENEWAL:
            self._SelectContractTypeCode("CDD")
        elif operation is ContractOperation.CDD_TO_CDI:
            self._SelectContractTypeCode("CDI")
        self._trial_user_modified = False
        self._RefreshOperationVisibility()
        self.RefreshContractRules()
        self.RefreshTrialProposal(force=True)
        if event:
            event.Skip()

    def OnPreviousContractChanged(self, event):
        self._trial_user_modified = False
        self.RefreshTrialProposal(force=True)
        if event:
            event.Skip()

    # ------------------------------------------------------------------
    # Période d'essai structurée

    def _BuildTrialControls(self):
        self.label_essai.Hide()
        self.periode_essai.Hide()
        self.aide_essai.Hide()

        self.check_trial = wx.CheckBox(self, -1, _(u"Prévoir une période d'essai"))
        self.label_trial_value = wx.StaticText(self, -1, _(u"Durée :"))
        self.trial_value = wx.SpinCtrl(self, -1, "", min=0, max=365, initial=0, size=(75, -1))
        self.choice_trial_unit = wx.Choice(self, -1, choices=[])
        for unit, label in TRIAL_UNIT_LABELS:
            self.choice_trial_unit.Append(_(label), unit.value)
        self.SelectChoice(self.choice_trial_unit, ProbationUnit.DAY.value)
        self.trial_help = wx.StaticText(self, -1, "")
        self.trial_help.SetForegroundColour("Grey")
        self.trial_help.Wrap(560)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(self.check_trial, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        row.Add(self.label_trial_value, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        row.Add(self.trial_value, 0, wx.RIGHT, 5)
        row.Add(self.choice_trial_unit, 0, wx.RIGHT, 8)
        self.sizer_essai.Add(row, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 7)
        self.sizer_essai.Add(self.trial_help, 0, wx.ALL | wx.EXPAND, 7)

        self.Bind(wx.EVT_CHECKBOX, self.OnTrialEnabledChanged, self.check_trial)
        self.Bind(wx.EVT_SPINCTRL, self.OnTrialManualChanged, self.trial_value)
        self.Bind(wx.EVT_CHOICE, self.OnTrialManualChanged, self.choice_trial_unit)

        data = self.GetGrandParent().dictContrats
        structured_value = data.get("trial_period_value")
        structured_unit = data.get("trial_period_unit")
        if structured_value is not None and structured_unit:
            self.check_trial.SetValue(int(structured_value) > 0)
            self.trial_value.SetValue(int(structured_value))
            self.SelectChoice(self.choice_trial_unit, structured_unit)
            self._trial_user_modified = True
        elif data.get("IDcontrat"):
            legacy = int(data.get("essai") or 0)
            self.check_trial.SetValue(legacy > 0)
            self.trial_value.SetValue(legacy)
            self.SelectChoice(self.choice_trial_unit, ProbationUnit.DAY.value)
            self._trial_user_modified = True
        self._EnableTrialControls()

    def _EnableTrialControls(self):
        enabled = self.check_trial.GetValue()
        self.label_trial_value.Enable(enabled)
        self.trial_value.Enable(enabled)
        self.choice_trial_unit.Enable(enabled)

    def OnTrialEnabledChanged(self, event):
        self._trial_user_modified = True
        self._EnableTrialControls()
        if event:
            event.Skip()

    def OnTrialManualChanged(self, event):
        self._trial_user_modified = True
        if event:
            event.Skip()

    def _CurrentContractType(self):
        selection = self.choice_type.GetSelection()
        if selection == -1:
            return ContractType.OTHER
        type_id = self.choice_type.GetClientData(selection)
        code = self.dictTypeCodes.get(type_id) or "OTHER"
        try:
            return ContractType(code)
        except ValueError:
            return ContractType.OTHER

    def _SelectedPreviousDates(self):
        previous_id = self.GetChoiceData(self.choice_previous_contract)
        if previous_id is None:
            return None, None
        return self._previous_contracts.get(int(previous_id), (None, None))

    def _BuildTrialProposal(self):
        operation = self._GetOperation()
        if operation is None:
            return None
        contract_type = self._CurrentContractType()
        if contract_type is ContractType.CDI and not self.IsCCNSSelected():
            return None
        start = self.GetReferenceDate()
        end = None
        if self.datepicker_date_fin.IsShown():
            try:
                end = datetime.date.fromisoformat(self.GetDatePickerValue(self.datepicker_date_fin))
            except ValueError:
                end = None
        previous_start, previous_end = self._SelectedPreviousDates()
        return propose_ccns_probation_period(
            contract_type=contract_type,
            operation=operation,
            start_date=start,
            end_date=end,
            ccns_group=self.GetChoiceData(self.choice_ccns_group),
            previous_contract_start=previous_start,
            previous_contract_end=previous_end,
        )

    def RefreshTrialProposal(self, force=False):
        if not self._modern_ready:
            return
        try:
            proposal = self._BuildTrialProposal()
        except Exception as err:
            proposal = None
            self.trial_help.SetLabel(_(u"Calcul automatique indisponible : %s") % err)

        if proposal is None:
            if not self.trial_help.GetLabel():
                self.trial_help.SetLabel(_(u"Durée à renseigner manuellement pour ce parcours."))
            self._EnableTrialControls()
            return

        if force or not self._trial_user_modified:
            self.check_trial.SetValue(proposal.value > 0)
            self.trial_value.SetValue(proposal.value)
            self.SelectChoice(self.choice_trial_unit, proposal.unit.value)
            self._trial_user_modified = False
        suffix = _(u" Proposition automatique ; la période d'essai reste facultative lorsqu'elle est juridiquement possible.")
        self.trial_help.SetLabel(_(proposal.reason) + suffix)
        self._EnableTrialControls()

    def _ValidateOperation(self):
        operation = self._GetOperation()
        data = self.GetGrandParent().dictContrats
        if operation is None:
            return bool(data.get("IDcontrat"))

        contract_type = self._CurrentContractType()
        previous_id = self.GetChoiceData(self.choice_previous_contract)
        if operation is ContractOperation.CDD_RENEWAL and contract_type is not ContractType.CDD:
            wx.MessageBox(_(u"Un renouvellement de CDD doit produire un CDD."), _(u"Nature de l'opération"), wx.OK | wx.ICON_ERROR, parent=self)
            return False
        if operation is ContractOperation.CDD_TO_CDI and contract_type is not ContractType.CDI:
            wx.MessageBox(_(u"Un passage CDD → CDI doit produire un CDI."), _(u"Nature de l'opération"), wx.OK | wx.ICON_ERROR, parent=self)
            return False
        if operation in (ContractOperation.CDD_RENEWAL, ContractOperation.CDD_TO_CDI):
            if previous_id is None:
                wx.MessageBox(_(u"Sélectionnez le CDD précédent."), _(u"Contrat précédent"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            previous_start, previous_end = self._SelectedPreviousDates()
            if previous_start is None or previous_end is None:
                return False
            expected_start = previous_end + datetime.timedelta(days=1)
            if self.GetReferenceDate() != expected_start:
                wx.MessageBox(
                    _(u"Le nouveau contrat doit suivre immédiatement le CDD précédent (%s attendu).") % expected_start.strftime("%d/%m/%Y"),
                    _(u"Continuité contractuelle"), wx.OK | wx.ICON_ERROR, parent=self,
                )
                return False
        return True

    def _StructuredTrial(self):
        if not self.check_trial.GetValue():
            return 0, ProbationUnit.DAY
        value = int(self.trial_value.GetValue())
        unit_raw = self.GetChoiceData(self.choice_trial_unit) or ProbationUnit.DAY.value
        return value, ProbationUnit(unit_raw)

    def _ValidateTrialMaximum(self):
        value, unit = self._StructuredTrial()
        try:
            proposal = self._BuildTrialProposal()
        except Exception:
            proposal = None
        if proposal is None or not proposal.automatic:
            return True
        entered_days = probation_calendar_days(start_date=self.GetReferenceDate(), value=value, unit=unit)
        max_days = probation_calendar_days(
            start_date=self.GetReferenceDate(), value=proposal.value, unit=proposal.unit
        )
        if entered_days > max_days:
            wx.MessageBox(
                _(u"La période d'essai saisie dépasse le maximum calculé pour ce parcours."),
                _(u"Période d'essai"), wx.OK | wx.ICON_ERROR, parent=self,
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Minimum salarial directement dans la case

    def _MaybePrefillSalary(self, amount):
        if amount is None or self._salary_prefill_guard:
            return
        amount = Decimal(amount).quantize(Decimal("0.01"))
        current = self._MonthlySalaryDecimal()
        if current is not None and (self._auto_salary_value is None or current != self._auto_salary_value):
            return
        self._salary_prefill_guard = True
        try:
            self.monthly_salary.SetValue(("%.2f" % amount).replace(".", ","))
            self._auto_salary_value = amount
        finally:
            self._salary_prefill_guard = False

    def RefreshCCNSPreview(self):
        super().RefreshCCNSPreview()
        if not self._modern_ready or not self.IsCCNSSelected():
            return
        group_code = self.GetChoiceData(self.choice_ccns_group)
        if not group_code:
            return
        choice = next((item for item in self.ccns_choices if item.code == group_code), None)
        if choice is None:
            return

        if choice.periodicity is SalaryMinimumPeriodicity.ANNUAL:
            self.label_monthly_salary.SetLabel(_(u"Rémunération brute annuelle :"))
            self.label_monthly_unit.SetLabel(_(u"€ brut / an"))
            self._MaybePrefillSalary(choice.minimum_amount)
            self.label_ccns_preview.SetLabel(
                _(u"Minimum CCNS annuel de référence à temps plein : %s €. Le minimum est appliqué au prorata des mois concernés.")
                % self._Money(choice.minimum_amount)
            )
            return

        self.label_monthly_salary.SetLabel(_(u"Rémunération brute mensuelle :"))
        self.label_monthly_unit.SetLabel(_(u"€ brut / mois"))
        try:
            preview = self.ccns_presenter.evaluate_monthly(
                group_code=group_code,
                reference_date=self.GetReferenceDate(),
                weekly_hours=Decimal(str(self.weekly_hours.GetValue())),
                remuneration_amount=Decimal("0.00"),
                territory=SmicTerritory.METROPOLITAN_FRANCE,
            )
        except Exception:
            return
        self._MaybePrefillSalary(preview.required_minimum_amount)
        # Recalcul avec la valeur préremplie afin que l'état affiche CONFORME.
        super().RefreshCCNSPreview()

    # ------------------------------------------------------------------
    # Événements legacy enrichis

    def CalcEssai(self):
        if self._modern_ready:
            self.RefreshTrialProposal()
            return
        return super().CalcEssai()

    def OnChoiceType(self, event):
        super().OnChoiceType(event)
        if self._modern_ready:
            self._trial_user_modified = False
            self.RefreshTrialProposal(force=True)

    def OnChoiceConvention(self, event):
        super().OnChoiceConvention(event)
        if self._modern_ready:
            self.RefreshTrialProposal()

    def OnCCNSFieldChanged(self, event):
        if self._modern_ready and event and event.GetEventObject() is self.monthly_salary and not self._salary_prefill_guard:
            current = self._MonthlySalaryDecimal()
            if self._auto_salary_value is not None and current != self._auto_salary_value:
                self._auto_salary_value = None
        super().OnCCNSFieldChanged(event)
        if self._modern_ready and event and event.GetEventObject() is self.choice_ccns_group:
            self._trial_user_modified = False
            self.RefreshTrialProposal(force=True)

    def OnContractDateChanged(self, event):
        super().OnContractDateChanged(event)
        if self._modern_ready:
            self._trial_user_modified = False
            self.RefreshTrialProposal(force=True)

    # ------------------------------------------------------------------

    def Validation(self):
        if not self._ValidateOperation() or not self._ValidateTrialMaximum():
            return False

        operation = self._GetOperation()
        trial_value, trial_unit = self._StructuredTrial()
        legacy_days = probation_calendar_days(
            start_date=self.GetReferenceDate(), value=trial_value, unit=trial_unit
        )

        # Le contrôleur historique ne connaît qu'un entier en jours et affiche
        # une confirmation lorsque la valeur vaut zéro. Zéro est pourtant le
        # résultat normal d'un renouvellement CDD ou d'un CDD→CDI dont la durée
        # antérieure absorbe tout l'essai : on évite uniquement cette fausse
        # alerte, puis on restaure la vraie valeur structurée après validation.
        expected_zero = False
        try:
            proposal = self._BuildTrialProposal()
            expected_zero = bool(proposal and proposal.automatic and proposal.value == 0)
        except Exception:
            pass
        self.periode_essai.SetValue(1 if expected_zero else legacy_days)

        group_code = self.GetChoiceData(self.choice_ccns_group)
        choice = next((item for item in self.ccns_choices if item.code == group_code), None)
        annual = bool(choice and choice.periodicity is SalaryMinimumPeriodicity.ANNUAL and self.IsCCNSSelected())
        annual_salary = self._MonthlySalaryDecimal() if annual else None
        if annual:
            if annual_salary is None or annual_salary <= Decimal("0"):
                wx.MessageBox(_(u"Vous devez saisir la rémunération brute annuelle."), _(u"CCNS"), wx.OK | wx.ICON_ERROR, parent=self)
                return False
            if Decimal(str(self.weekly_hours.GetValue())) == Decimal("35") and annual_salary < choice.minimum_amount:
                wx.MessageBox(
                    _(u"La rémunération annuelle saisie est inférieure au minimum CCNS du groupe."),
                    _(u"Rémunération non conforme"), wx.OK | wx.ICON_ERROR, parent=self,
                )
                return False

        validation = super().Validation()
        if not validation:
            return False

        data = self.GetGrandParent().dictContrats
        data["operation_type"] = operation.value if operation else None
        data["previous_contract_id"] = self.GetChoiceData(self.choice_previous_contract) if operation in (
            ContractOperation.CDD_RENEWAL, ContractOperation.CDD_TO_CDI
        ) else None
        data["trial_period_value"] = trial_value
        data["trial_period_unit"] = trial_unit.value
        data["essai"] = legacy_days
        if annual:
            data["gross_annual_salary"] = float(annual_salary)
            data["gross_monthly_salary"] = None
        else:
            data["gross_annual_salary"] = None
        return True
