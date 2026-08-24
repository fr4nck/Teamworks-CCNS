#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

from Utils import UTILS_Interface

try:
    from Ol import OL_Base
except Exception:
    OL_Base = None


def _blend(foreground, background, ratio):
    """Mélange deux couleurs wx pour produire une surface d'état discrète."""
    ratio = max(0.0, min(1.0, float(ratio)))
    inverse = 1.0 - ratio
    return wx.Colour(
        int(round(foreground.Red() * ratio + background.Red() * inverse)),
        int(round(foreground.Green() * ratio + background.Green() * inverse)),
        int(round(foreground.Blue() * ratio + background.Blue() * inverse)),
    )


def _severity_colours(severity):
    palette = UTILS_Interface.GetPalette()
    role = {
        "blocking": "danger",
        "warning": "warning",
        "ok": "success",
    }.get(severity, "on_surface")
    foreground = palette[role]
    background = _blend(foreground, palette["surface_container_lowest"], 0.12)
    return background, foreground


class Track(object):
    def __init__(self, donnees):
        self.IDcontrat = donnees.get("IDcontrat")
        self.nom_complet = donnees.get("nom_complet", "")
        self.classification = donnees.get("classification", "")
        self.type_contrat = donnees.get("type_contrat", "")
        self.salaire_base = donnees.get("salaire_base")
        self.salary_control_status_label = donnees.get("salary_control_status_label", "")
        self.remuneration_amount_label = donnees.get("remuneration_amount_label", "")
        self.applicable_minimum_amount_label = donnees.get("applicable_minimum_amount_label", "")
        self.minimum_source_label = donnees.get("minimum_source_label", "")
        self.shortfall_amount_label = donnees.get("shortfall_amount_label", "")
        self.anomalies = donnees.get("anomalies", [])
        self.messages = donnees.get("messages", [])
        self.severity_label = donnees.get("severity_label", "ok")

    def GetListeAnomalies(self):
        return ", ".join(self.anomalies) if self.anomalies else ""

    def GetNbAnomalies(self):
        return len(self.anomalies)

    def GetMessages(self):
        return " | ".join(self.messages)

    def GetSeverityLabel(self):
        labels = {
            "blocking": "Bloquant",
            "warning": "À revoir",
            "ok": "OK",
        }
        return labels.get(self.severity_label, self.severity_label)

    def HasAnomalies(self):
        return bool(self.anomalies)

    def HasBlockingHint(self):
        return self.severity_label == "blocking"


if OL_Base:
    class ListView(OL_Base.ListView):
        def __init__(self, *args, **kwds):
            self.donnees = kwds.pop("donnees", [])
            OL_Base.ListView.__init__(self, *args, **kwds)
            self.MAJ()

        def InitObjectListView(self):
            def fmt_salaire(track):
                if track.salaire_base in (None, ""):
                    return ""
                try:
                    return "%.2f" % float(track.salaire_base)
                except Exception:
                    return str(track.salaire_base)

            self.SetColumns([
                OL_Base.ColumnDefn(u"Nom", "left", 180, "nom_complet"),
                OL_Base.ColumnDefn(u"Gravité", "left", 90, "GetSeverityLabel"),
                OL_Base.ColumnDefn(u"ID", "left", 60, "IDcontrat"),
                OL_Base.ColumnDefn(u"Classification", "left", 90, "classification"),
                OL_Base.ColumnDefn(u"Type", "left", 90, "type_contrat"),
                OL_Base.ColumnDefn(u"Salaire base", "right", 90, fmt_salaire),
                OL_Base.ColumnDefn(u"Statut salarial", "left", 110, "salary_control_status_label"),
                OL_Base.ColumnDefn(u"Rémunération contrôlée", "right", 145, "remuneration_amount_label"),
                OL_Base.ColumnDefn(u"Minimum applicable", "right", 130, "applicable_minimum_amount_label"),
                OL_Base.ColumnDefn(u"Source", "left", 100, "minimum_source_label"),
                OL_Base.ColumnDefn(u"Écart", "right", 100, "shortfall_amount_label"),
                OL_Base.ColumnDefn(u"Nb anomalies", "center", 90, "GetNbAnomalies"),
                OL_Base.ColumnDefn(u"Anomalies", "left", 220, "GetListeAnomalies"),
                OL_Base.ColumnDefn(u"Messages", "left", 360, "GetMessages"),
            ])
            self.SetEmptyListMsg(u"Aucun résultat d'audit")
            self.cellEditMode = False

        def _apply_row_style(self, index, track):
            try:
                background, foreground = _severity_colours(track.severity_label)
                self.SetItemBackgroundColour(index, background)
                self.SetItemTextColour(index, foreground)
            except Exception:
                pass

        def MAJ(self):
            tracks = [Track(item) for item in self.donnees]
            self.SetObjects(tracks)
            for index, track in enumerate(tracks):
                self._apply_row_style(index, track)
else:
    class ListView(wx.ListCtrl):
        def __init__(self, parent, donnees=None):
            wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
            self.InsertColumn(0, "Nom", width=180)
            self.InsertColumn(1, "Gravité", width=90)
            self.InsertColumn(2, "ID", width=60)
            self.InsertColumn(3, "Classification", width=90)
            self.InsertColumn(4, "Type", width=90)
            self.InsertColumn(5, "Salaire base", width=90)
            self.InsertColumn(6, "Statut salarial", width=110)
            self.InsertColumn(7, "Rémunération contrôlée", width=145)
            self.InsertColumn(8, "Minimum applicable", width=130)
            self.InsertColumn(9, "Source", width=100)
            self.InsertColumn(10, "Écart", width=100)
            self.InsertColumn(11, "Nb anomalies", width=90)
            self.InsertColumn(12, "Anomalies", width=220)
            self.InsertColumn(13, "Messages", width=360)
            self.donnees = donnees or []
            self.MAJ()

        def _apply_row_style(self, index, item):
            try:
                background, foreground = _severity_colours(item.get("severity_label", "ok"))
                self.SetItemBackgroundColour(index, background)
                self.SetItemTextColour(index, foreground)
            except Exception:
                pass

        def MAJ(self):
            self.DeleteAllItems()
            for item in self.donnees:
                idx = self.InsertItem(self.GetItemCount(), item.get("nom_complet", ""))
                labels = {"blocking": "Bloquant", "warning": "À revoir", "ok": "OK"}
                self.SetItem(idx, 1, labels.get(item.get("severity_label", "ok"), ""))
                self.SetItem(idx, 2, str(item.get("IDcontrat", "")))
                self.SetItem(idx, 3, item.get("classification", "") or "")
                self.SetItem(idx, 4, item.get("type_contrat", "") or "")
                salaire = item.get("salaire_base")
                self.SetItem(idx, 5, "" if salaire is None else "%.2f" % float(salaire))
                self.SetItem(idx, 6, item.get("salary_control_status_label", ""))
                self.SetItem(idx, 7, item.get("remuneration_amount_label", ""))
                self.SetItem(idx, 8, item.get("applicable_minimum_amount_label", ""))
                self.SetItem(idx, 9, item.get("minimum_source_label", ""))
                self.SetItem(idx, 10, item.get("shortfall_amount_label", ""))
                anomalies = item.get("anomalies", [])
                self.SetItem(idx, 11, str(len(anomalies)))
                self.SetItem(idx, 12, ", ".join(anomalies))
                self.SetItem(idx, 13, " | ".join(item.get("messages", [])))
                self._apply_row_style(idx, item)
