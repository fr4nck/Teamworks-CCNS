"""Exécuter les vrais constructeurs avec des événements wx synchrones et sans base réelle."""

import ast
import calendar
import datetime
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "teamworks/Dlg/DLG_Selection_periode.py"
ROWS = [(1, "Vacances de test", "2024", "2024-02-10", "2024-03-03")]
INITIAL = datetime.date(2001, 1, 1)
EXPECTED = (datetime.date(2024, 2, 10), datetime.date(2024, 3, 3))


def _load_classes(namespace, source=SOURCE):
    tree = ast.parse(source.read_text(encoding="utf-8"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    exec(compile(ast.Module(body=classes, type_ignores=[]), str(source), "exec"), namespace)
    return namespace


def _dialog(phase=None, event_type="selected", rows=None):
    """Les panneaux restent stricts : ils ne possèdent aucun champ du dialogue."""
    emitted = []

    class Window:
        def __init__(self, parent=None, *args, **kwargs):
            self.native_parent = parent
            self.bindings = {}

        def Bind(self, kind, handler, *args):
            self.bindings[kind] = handler

        def SetBackgroundColour(self, value):
            pass

        def SetForegroundColour(self, value):
            pass

        def SetSizer(self, sizer):
            pass

    class Section(Window):
        def __init__(self, parent, **kwargs):
            super().__init__(parent)
            self.content = Window(self)

        def GetContentPanel(self):
            return self.content

    class ListCtrl(Window):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.selected = -1
            self.widths = {}

        def emit(self):
            event = SimpleNamespace(Skip=Mock())
            handler = self.bindings.get(event_type)
            emitted.append((handler is not None, event))
            if handler is not None:
                handler(event)

        def Bind(self, kind, handler, *args):
            super().Bind(kind, handler, *args)
            if phase == "bind" and kind == event_type:
                self.selected = 0
                self.emit()

        def InsertColumn(self, *args):
            pass

        def DeleteAllItems(self):
            self.selected = -1

        def InsertItem(self, index, text):
            if phase == "insert":
                self.selected = index
                self.emit()

        def SetItem(self, *args):
            pass

        def SetItemData(self, *args):
            pass

        def GetClientSize(self):
            return SimpleNamespace(width=500)

        def SetColumnWidth(self, index, width):
            self.widths[index] = width

        def GetColumnWidth(self, index):
            return self.widths[index]

        def GetFirstSelected(self):
            return self.selected

        def SetMinSize(self, size):
            if phase == "min_size":
                self.selected = 0
                self.emit()

    class Choice(Window):
        def __init__(self, *args, choices, **kwargs):
            super().__init__(*args, **kwargs)
            self.choices = choices
            self.selection = -1

        def SetSelection(self, index):
            self.selection = index

        def GetSelection(self):
            return self.selection

        def SetStringSelection(self, text):
            self.selection = self.choices.index(text)

    class DateTime:
        def Set(self, day, month, year):
            self.date = datetime.date(year, month + 1, day)

        def GetYear(self):
            return self.date.year

        def GetMonth(self):
            return self.date.month - 1

        def GetDay(self):
            return self.date.day

    class DatePicker(Window):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.value = DateTime()
            self.value.date = INITIAL

        def SetValue(self, value):
            self.value = value

        def GetValue(self):
            return self.value

    sizer = SimpleNamespace(**{name: Mock() for name in (
        "Add", "AddSpacer", "AddStretchSpacer",
    )})
    wx = SimpleNamespace(
        Dialog=Window, ListCtrl=ListCtrl, Choice=Choice, DateTime=DateTime,
        BoxSizer=lambda *args: sizer,
        EVT_LIST_ITEM_SELECTED="selected", EVT_LIST_ITEM_ACTIVATED="activated",
        EVT_SIZE="size", EVT_BUTTON="button", EVT_CHOICE="choice",
        **{name: 0 for name in (
            "LC_REPORT", "LC_SINGLE_SEL", "LC_HRULES", "DEFAULT_DIALOG_STYLE",
            "RESIZE_BORDER", "VERTICAL", "HORIZONTAL", "EXPAND", "RIGHT",
            "LEFT", "TOP", "BOTTOM", "ID_CANCEL",
        )},
    )
    db = Mock()
    db.ResultatReq.return_value = ROWS if rows is None else rows
    namespace = {
        "wx": wx, "datetime": datetime, "calendar": calendar,
        "_": lambda text: text, "GestionDB": SimpleNamespace(DB=lambda: db),
        "DatePickerCtrl": DatePicker, "DP_DROPDOWN": 0,
        "CTRL_Section": SimpleNamespace(Section=Section),
        "CTRL_Texte": SimpleNamespace(BodySecondary=Window, Label=Window),
        "CTRL_Bouton_image": SimpleNamespace(CTRL=Window),
        "UTILS_Interface": SimpleNamespace(GetToken=lambda name: name),
        "UTILS_Styles": SimpleNamespace(
            Scale=lambda value: value, GetLayoutSpacing=lambda name: 8,
            ApplyWindowProfile=lambda *args: None,
        ),
    }
    _load_classes(namespace)
    dialog = namespace["SelectionPeriode"](None)
    db.Close.assert_called_once_with()
    return dialog, emitted


@pytest.mark.parametrize("event_type", ["selected", "activated"])
def test_population_does_not_dispatch_selection_before_rows_are_ready(event_type):
    dialog, emitted = _dialog("insert", event_type)
    assert [handled for handled, event in emitted] == [False]
    assert dialog.GetDates() == (INITIAL, INITIAL)


@pytest.mark.parametrize("phase", ["bind", "min_size"])
@pytest.mark.parametrize("event_type", ["selected", "activated"])
def test_early_selection_during_construction_updates_dialog_not_section(phase, event_type):
    dialog, emitted = _dialog(phase, event_type)
    assert dialog.ctrl_vacances.native_parent is dialog.section_vacances.GetContentPanel()
    assert [handled for handled, event in emitted] == [True]
    emitted[0][1].Skip.assert_called_once_with()
    assert dialog.GetDates() == EXPECTED


@pytest.mark.parametrize("event_type", ["selected", "activated"])
def test_selection_after_opening_clears_calendar_and_copies_exact_dates(event_type):
    dialog, _ = _dialog(event_type=event_type)
    dialog.ctrl_mois.SetSelection(5)
    dialog.ctrl_annee.SetStringSelection("2025")
    dialog.ctrl_vacances.selected = 0
    dialog.ctrl_vacances.emit()
    assert dialog.ctrl_mois.GetSelection() == 0
    assert dialog.ctrl_annee.GetSelection() == 0
    assert dialog.GetDates() == EXPECTED


@pytest.mark.parametrize("index", [-1, len(ROWS)])
def test_invalid_selection_preserves_dates_and_calendar(index):
    dialog, _ = _dialog()
    dialog.ctrl_mois.SetSelection(5)
    dialog.ctrl_vacances.selected = index
    dialog.ctrl_vacances.emit()
    assert dialog.ctrl_mois.GetSelection() == 5
    assert dialog.GetDates() == (INITIAL, INITIAL)


def test_empty_list_and_calendar_selection_keep_existing_date_rules():
    dialog, _ = _dialog(rows=[])
    dialog.ctrl_vacances.emit()
    assert dialog.GetDates() == (INITIAL, INITIAL)
    dialog.ctrl_annee.SetStringSelection("2024")
    dialog.On_maj_annee(None)
    assert dialog.GetDates() == (datetime.date(2024, 1, 1), datetime.date(2024, 12, 31))
    dialog.ctrl_mois.SetSelection(2)
    dialog.On_maj_mois(None)
    assert dialog.GetDates() == (datetime.date(2024, 2, 1), datetime.date(2024, 2, 29))


@pytest.mark.skipif(sys.platform != "win32", reason="Contrôles wx natifs Windows")
def test_native_windows_selection_before_list_constructor_returns(monkeypatch):
    wx = pytest.importorskip("wx")
    from wx.adv import DatePickerCtrl, DP_DROPDOWN

    app = wx.App.Get() or wx.App(False)
    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda *error: errors.append(error))
    text = lambda parent, label: wx.StaticText(parent, label=label)
    styles = SimpleNamespace(
        Scale=lambda value: value, GetLayoutSpacing=lambda name: 8,
        ApplyWindowProfile=lambda window, profile: window.Layout(),
    )
    interface = SimpleNamespace(GetToken=lambda name: wx.Colour("white"))
    section_scope = _load_classes({
        "wx": wx, "UTILS_Interface": interface, "UTILS_Styles": styles,
        "CTRL_Texte": SimpleNamespace(**{name: text for name in (
            "H2", "H3", "H4", "H5", "H6", "BodySecondary",
        )}),
    }, SOURCE.parents[1] / "Ctrl/CTRL_Section.py")
    db = Mock()
    db.ResultatReq.return_value = ROWS
    scope = _load_classes({
        "wx": wx, "calendar": calendar, "datetime": datetime,
        "_": lambda value: value, "DatePickerCtrl": DatePickerCtrl,
        "DP_DROPDOWN": DP_DROPDOWN, "GestionDB": SimpleNamespace(DB=lambda: db),
        "CTRL_Section": SimpleNamespace(Section=section_scope["Section"]),
        "CTRL_Texte": SimpleNamespace(BodySecondary=text, Label=text),
        "CTRL_Bouton_image": SimpleNamespace(
            CTRL=lambda parent, texte, id=wx.ID_ANY: wx.Button(parent, id, texte),
        ),
        "UTILS_Interface": interface, "UTILS_Styles": styles,
    })
    delivered = []

    class EarlyList(scope["ListCtrl_vacances"]):
        def __init__(self, *args):
            super().__init__(*args)
            self.Select(0)
            for kind in (wx.EVT_LIST_ITEM_SELECTED, wx.EVT_LIST_ITEM_ACTIVATED):
                event = wx.ListEvent(kind.typeId, self.GetId())
                event.SetEventObject(self)
                event.m_itemIndex = 0
                self.GetEventHandler().ProcessEvent(event)
                delivered.append(self.owner.GetDates())

    scope["ListCtrl_vacances"] = EarlyList
    dialog = scope["SelectionPeriode"](None)
    try:
        assert delivered == [EXPECTED, EXPECTED]
        assert dialog.ctrl_vacances.GetParent() is dialog.section_vacances.GetContentPanel()
        dialog.Show()
        app.Yield()
        assert dialog.GetDates() == EXPECTED
        assert errors == []
    finally:
        dialog.Destroy()
        app.Yield()
