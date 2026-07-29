# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ObjectListView module initialization
# Author:       Phillip Piper
# Created:      29 February 2008
# Copyright:    (c) 2008 by Phillip Piper
# License:      wxWindows license
#----------------------------------------------------------------------------
# Change log:
# 2008/08/02  JPP   Added list printing material
# 2008/07/24  JPP   Added list group related material
# 2008/06/19  JPP   Added sort event related material
# 2008/04/11  JPP   Initial Version

"""
An ObjectListView provides a more convienent and powerful interface to a ListCtrl.
"""

import time


# ObjectListView 1.3.2 utilise encore time.clock(), supprimé de Python 3.8.
# Une horloge monotone conserve la sémantique attendue pour les temporisations
# de rafraîchissement sans dépendre de l'heure système.
if not hasattr(time, "clock"):
    time.clock = time.monotonic


__version__ = '1.3.2'
__copyright__ = "Copyright (c) 2008 Phillip Piper (phillip_piper@bigfoot.com)"

from . ObjectListView import ObjectListView, VirtualObjectListView, ColumnDefn, FastObjectListView, GroupListView, ListGroup, BatchedUpdate, NamedImageList
from . OLVEvent import CellEditFinishedEvent, CellEditFinishingEvent, CellEditStartedEvent, CellEditStartingEvent, SortEvent
from . OLVEvent import EVT_CELL_EDIT_STARTING, EVT_CELL_EDIT_STARTED, EVT_CELL_EDIT_FINISHING, EVT_CELL_EDIT_FINISHED, EVT_SORT
from . OLVEvent import EVT_COLLAPSING, EVT_COLLAPSED, EVT_EXPANDING, EVT_EXPANDED, EVT_GROUP_CREATING, EVT_GROUP_SORT, EVT_ITEM_CHECKED
from . CellEditor import CellEditorRegistry, MakeAutoCompleteTextBox, MakeAutoCompleteComboBox
from . ListCtrlPrinter import ListCtrlPrinter, ReportFormat, BlockFormat, LineDecoration, RectangleDecoration, ImageDecoration

from . import Filter


def _resize_space_filling_columns_int(self):
    """Redimensionne les colonnes extensibles avec des largeurs wxPython entières."""
    if True not in set(column.isSpaceFilling for column in self.columns):
        return

    total_fixed_width = sum(
        self.GetColumnWidth(index)
        for index, column in enumerate(self.columns)
        if not column.isSpaceFilling
    )
    free_space = max(0, self.GetClientSize()[0] - total_fixed_width)
    total_proportion = sum(
        column.freeSpaceProportion
        for column in self.columns
        if column.isSpaceFilling
    )
    if not total_proportion:
        return

    columns_to_resize = []
    for index, column in enumerate(self.columns):
        if not column.isSpaceFilling:
            continue
        new_width = free_space * column.freeSpaceProportion / total_proportion
        bounded_width = int(round(column.CalcBoundedWidth(new_width)))
        if int(round(new_width)) == bounded_width:
            columns_to_resize.append((index, column))
        else:
            free_space -= bounded_width
            total_proportion -= column.freeSpaceProportion
            if self.GetColumnWidth(index) != bounded_width:
                self.SetColumnWidth(index, bounded_width)

    if not total_proportion:
        return
    for index, column in columns_to_resize:
        new_width = free_space * column.freeSpaceProportion / total_proportion
        bounded_width = int(round(column.CalcBoundedWidth(new_width)))
        if self.GetColumnWidth(index) != bounded_width:
            self.SetColumnWidth(index, bounded_width)


for _list_class in (ObjectListView, VirtualObjectListView, FastObjectListView, GroupListView):
    _list_class._ResizeSpaceFillingColumns = _resize_space_filling_columns_int


__all__ = [
    "BatchedUpdate",
    "BlockFormat",
    "CellEditFinishedEvent",
    "CellEditFinishingEvent",
    "CellEditorRegistry",
    "CellEditStartedEvent",
    "CellEditStartingEvent",
    "ColumnDefn",
    "EVT_CELL_EDIT_FINISHED",
    "EVT_CELL_EDIT_FINISHING",
    "EVT_CELL_EDIT_STARTED",
    "EVT_CELL_EDIT_STARTING",
    "EVT_COLLAPSED",
    "EVT_COLLAPSING",
    "EVT_EXPANDED",
    "EVT_EXPANDING",
    "EVT_GROUP_CREATING",
    "EVT_GROUP_SORT"
    "EVT_SORT",
    "Filter",
    "FastObjectListView",
    "GroupListView",
    "ListGroup",
    "ImageDecoration",
    "MakeAutoCompleteTextBox",
    "MakeAutoCompleteComboBox",
    "ListGroup",
    "ObjectListView",
    "ListCtrlPrinter",
    "RectangleDecoration",
    "ReportFormat",
    "SortEvent",
    "VirtualObjectListView",
]
