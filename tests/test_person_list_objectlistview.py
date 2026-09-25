import sys
from dataclasses import dataclass

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="ObjectListView integration contract is exercised on Windows",
)

wx = pytest.importorskip("wx")
olv_module = pytest.importorskip("ObjectListView")
ObjectListView = olv_module.ObjectListView
ColumnDefn = olv_module.ColumnDefn
Filter = olv_module.Filter


@dataclass
class PersonRow:
    IDpersonne: int
    nom: str
    prenom: str
    ville: str


def _rows():
    cities = ("Rennes", "Brest", "Vannes", "Lorient", "Quimper")
    rows = []
    for index in range(1, 51):
        person_id = index * 10
        nom = "DUPONT" if index % 7 == 0 else "MARTIN%02d" % index
        rows.append(PersonRow(person_id, nom, "Prenom%02d" % index, cities[index % len(cities)]))
    return rows


def _replacement_rows():
    return [
        PersonRow(row.IDpersonne, row.nom, row.prenom, row.ville)
        for row in _rows()
    ]


def _flush_wx_events():
    app = wx.GetApp()
    while app.Pending():
        app.Dispatch()
    app.ProcessIdle()


@pytest.fixture(scope="session")
def wx_app():
    app = wx.GetApp() or wx.App(False)
    yield app


@pytest.fixture
def person_list(wx_app):
    frame = wx.Frame(None, size=(560, 260))
    control = ObjectListView(
        frame,
        style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
    )
    columns = [
        ColumnDefn("ID", "left", 60, "IDpersonne"),
        ColumnDefn("Nom", "left", 140, "nom"),
        ColumnDefn("Prenom", "left", 140, "prenom"),
        ColumnDefn("Ville", "left", 140, "ville"),
    ]
    control.SetColumns(columns)
    control.SetObjects(_rows())
    frame.Show()
    _flush_wx_events()
    try:
        yield control
    finally:
        frame.Destroy()
        _flush_wx_events()


def _find_by_id(control, person_id):
    return next(
        (row for row in control.GetObjects() if row.IDpersonne == person_id),
        None,
    )


def _visible_ids(control):
    return [row.IDpersonne for row in control.GetFilteredObjects()]


def test_replacing_objects_requires_selection_restoration_by_person_id(person_list):
    old = _find_by_id(person_list, 420)
    person_list.SelectObject(old, deselectOthers=True, ensureVisible=True)
    assert person_list.GetSelectedObject() is old

    person_list.SetObjects(_replacement_rows())
    replacement = _find_by_id(person_list, 420)
    person_list.SelectObject(replacement, deselectOthers=True, ensureVisible=True)

    selected = person_list.GetSelectedObject()
    assert selected.IDpersonne == 420
    assert selected is replacement
    assert selected is not old


def test_setobjects_preserves_active_sort_without_rebuilding_columns(person_list):
    city_column = person_list.columns[3]
    person_list.SetSortColumn(city_column)
    person_list.sortAscending = False
    person_list.RepopulateList()
    expected_sort_column = person_list.GetSortColumn()

    person_list.SetObjects(_replacement_rows())

    assert person_list.GetSortColumn() is expected_sort_column
    visible_cities = [row.ville for row in person_list.GetFilteredObjects()]
    assert visible_cities == sorted(visible_cities, reverse=True)


def test_setobjects_preserves_column_widths(person_list):
    person_list.SetColumnWidth(1, 317)
    person_list.SetColumnWidth(3, 183)

    person_list.SetObjects(_replacement_rows())

    assert person_list.GetColumnWidth(1) == 317
    assert person_list.GetColumnWidth(3) == 183


def test_real_text_filter_survives_object_replacement(person_list):
    text_filter = Filter.TextSearch(person_list, person_list.columns[1:4])
    text_filter.SetText("dupont")
    person_list.SetFilter(text_filter)
    person_list.RepopulateList()
    expected = _visible_ids(person_list)
    assert expected

    person_list.SetObjects(_replacement_rows())

    assert _visible_ids(person_list) == expected


def test_refresh_can_restore_visible_region_when_selection_does_not_move(person_list):
    target = _find_by_id(person_list, 420)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)
    _flush_wx_events()
    top_before = person_list.GetTopItem()
    top_id = person_list.GetObjectAt(top_before).IDpersonne

    person_list.SetObjects(_replacement_rows())
    top_replacement = _find_by_id(person_list, top_id)
    top_index = person_list.GetIndexOf(top_replacement)
    person_list.EnsureVisible(top_index)
    _flush_wx_events()

    assert person_list.GetObjectAt(person_list.GetTopItem()).IDpersonne == top_id


def test_reselecting_same_object_documents_real_selection_event_behavior(person_list):
    target = _find_by_id(person_list, 420)
    events = []

    def on_selected(event):
        events.append(event.GetIndex())
        event.Skip()

    person_list.Bind(wx.EVT_LIST_ITEM_SELECTED, on_selected)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)
    _flush_wx_events()
    events.clear()

    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)
    _flush_wx_events()

    # This assertion intentionally documents the wx/OLV behavior used by Teamworks:
    # callers must not rely on reselection to refresh the Personnes summary.
    assert events == []



def test_hidden_selected_id_is_restored_when_refresh_makes_it_visible(person_list):
    person_id = 420
    target = _find_by_id(person_list, person_id)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)

    text_filter = Filter.TextSearch(person_list, person_list.columns[1:4])
    text_filter.SetText("rennes")
    person_list.SetFilter(text_filter)
    person_list.RepopulateList()
    _flush_wx_events()
    assert person_id not in _visible_ids(person_list)

    replacement_rows = _replacement_rows()
    replacement = next(row for row in replacement_rows if row.IDpersonne == person_id)
    replacement.ville = "Rennes"
    person_list.SetObjects(replacement_rows)
    person_list.SelectObject(replacement, deselectOthers=True, ensureVisible=True)
    _flush_wx_events()

    assert person_list.GetSelectedObject().IDpersonne == person_id
    assert person_id in _visible_ids(person_list)


def test_removed_selected_id_leaves_no_selection(person_list):
    person_id = 420
    target = _find_by_id(person_list, person_id)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)

    person_list.SetObjects([
        row for row in _replacement_rows() if row.IDpersonne != person_id
    ])
    person_list.DeselectAll()
    _flush_wx_events()

    assert _find_by_id(person_list, person_id) is None
    assert person_list.GetSelectedObject() is None


def test_teamworks_maj_restores_selected_identity_without_rebuilding_view(person_list, monkeypatch):
    from Ol import OL_personnes

    person_id = 420
    target = _find_by_id(person_list, person_id)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)

    calls = {"init_view": 0, "summary": []}
    replacement_rows = _replacement_rows()

    monkeypatch.setattr(person_list, "InitModel", lambda: setattr(person_list, "donnees", replacement_rows))
    monkeypatch.setattr(
        person_list,
        "InitObjectListView",
        lambda: calls.__setitem__("init_view", calls["init_view"] + 1),
    )
    monkeypatch.setattr(
        person_list,
        "SyncSummary",
        lambda selected_id=None: calls["summary"].append(selected_id),
    )

    OL_personnes.ListView.MAJ(person_list, IDpersonne=person_id)

    selected = person_list.GetSelectedObject()
    assert calls["init_view"] == 0
    assert selected.IDpersonne == person_id
    assert selected is _find_by_id(person_list, person_id)
    assert calls["summary"] == [person_id]


def test_teamworks_maj_clears_missing_identity_and_summary(person_list, monkeypatch):
    from Ol import OL_personnes

    person_id = 420
    target = _find_by_id(person_list, person_id)
    person_list.SelectObject(target, deselectOthers=True, ensureVisible=True)

    replacement_rows = [
        row for row in _replacement_rows() if row.IDpersonne != person_id
    ]
    summary_calls = []

    monkeypatch.setattr(person_list, "InitModel", lambda: setattr(person_list, "donnees", replacement_rows))
    monkeypatch.setattr(
        person_list,
        "SyncSummary",
        lambda selected_id=None: summary_calls.append(selected_id),
    )

    OL_personnes.ListView.MAJ(person_list, IDpersonne=person_id)

    assert person_list.GetSelectedObject() is None
    assert summary_calls == [None]
