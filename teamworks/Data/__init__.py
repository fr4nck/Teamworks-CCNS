# -*- coding: utf-8 -*-
"""Composition du schéma canonique Teamworks."""

from . import DATA_Tables
from .DATA_Tables_tw184 import ApplyContractSchema as _ApplyContractSchema

_ApplyContractSchema(DATA_Tables.DB_DATA)
del _ApplyContractSchema
