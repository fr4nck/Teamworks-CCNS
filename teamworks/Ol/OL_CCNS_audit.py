#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import wx

try:
    from Ol import OL_Base
except Exception:
    OL_Base = None


class Track(object):
    def __init__(self, donnees):
        self.IDcontrat = donnees.get("IDcontrat")
        self.nom_complet = donnees.get("nom_complet", "")
        self.classification = donnees.get("classification", "")
        self.type_contrat = donnees.get("type_contrat", "")
        self.salaire_base = donnees.get("salaire_base")
        self.anomalies = donnees.get("anomalies", [])
        self.messages = donnees.get("messages", [])

    def GetListeAnomalies(self):
        return ", ".join(self.anomalies) if self.anomalies else ""

    def GetNbAnomalies(self):
        return len(self.anomalies)

    def GetMessages(self):
        return " | ".join(self.messages)


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
                OL_Base.ColumnDefn(u"ID", "left", 60, "IDcontrat"),
                OL_Base.ColumnDefn(u"Nom", "left", 180, "nom_complet"),
                OL_Base.ColumnDefn(u"Classification", "left", 90, "classification"),
                OL_Base.ColumnDefn(u"Type", "left", 90, "type_contrat"),
                OL_Base.ColumnDefn(u"Salaire base", "right", 90, fmt_salaire),
                OL_Base.ColumnDefn(u"Nb anomalies", "center", 90, "GetNbAnomalies"),
                OL_Base.ColumnDefn(u"Anomalies", "left", 220, "GetListeAnomalies"),
                OL_Base.ColumnDefn(u"Messages", "left", 360, "GetMessages"),
            ])
            self.SetEmptyListMsg(u"Aucun resultat d'audit")
            self.cellEditMode = False

        def MAJ(self):
            tracks = [Track(item) for item in self.donnees]
            self.SetObjects(tracks)
else:
    class ListView(wx.ListCtrl):
        def __init__(self, parent, donnees=None):
            wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
            self.InsertColumn(0, "ID", width=60)
            self.InsertColumn(1, "Nom", width=180)
            self.InsertColumn(2, "Classification", width=90)
            self.InsertColumn(3, "Type", width=90)
            self.InsertColumn(4, "Salaire base", width=90)
            self.InsertColumn(5, "Nb anomalies", width=90)
            self.InsertColumn(6, "Anomalies", width=220)
            self.InsertColumn(7, "Messages", width=360)
            self.donnees = donnees or []
            self.MAJ()

        def MAJ(self):
            self.DeleteAllItems()
            for item in self.donnees:
                idx = self.InsertItem(self.GetItemCount(), str(item.get("IDcontrat", "")))
                self.SetItem(idx, 1, item.get("nom_complet", ""))
                self.SetItem(idx, 2, item.get("classification", "") or "")
                self.SetItem(idx, 3, item.get("type_contrat", "") or "")
                salaire = item.get("salaire_base")
                self.SetItem(idx, 4, "" if salaire is None else "%.2f" % float(salaire))
                anomalies = item.get("anomalies", [])
                self.SetItem(idx, 5, str(len(anomalies)))
                self.SetItem(idx, 6, ", ".join(anomalies))
                self.SetItem(idx, 7, " | ".join(item.get("messages", [])))
