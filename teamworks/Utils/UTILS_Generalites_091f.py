#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Correctifs de saisie non bloquante pour la fiche Généralités.

Ce module reste volontairement petit : il neutralise les anciens automatismes
Villes.db3 qui modifiaient la saisie pendant la frappe ou affichaient une boîte
de dialogue au focus perdu. Le bouton Rechercher conserve l'assistance française,
mais l'utilisateur reste toujours maître des valeurs saisies.
"""

import wx


def _unbind(control, event, handler):
    try:
        control.Unbind(event, handler=handler)
    except Exception:
        pass


def _country_is_france(panel):
    try:
        pays = panel.Recherche_Pays(IDpays=panel.IDpays_naiss)
        return bool(pays and str(pays[2]).strip().casefold() == "france")
    except Exception:
        return True


def stabilise(panel):
    """Rend adresse et lieux éditables sans validation française bloquante."""
    if getattr(panel, "_teamworks_generalites_091f", False):
        return
    panel._teamworks_generalites_091f = True

    for name in ("text_adresse", "text_cp", "text_ville", "text_ville_naiss"):
        control = getattr(panel, name, None)
        if control is None:
            continue
        try:
            control.Enable(True)
        except Exception:
            pass
        try:
            control.SetEditable(True)
        except Exception:
            pass

    # Résidence : la saisie est libre. La recherche explicite reste disponible
    # via le bouton Rechercher et remplit toujours CP/ville lorsqu'on la demande.
    _unbind(panel.text_ville, wx.EVT_TEXT, panel.VilleText2)
    _unbind(panel.text_ville, wx.EVT_CHAR, panel.VilleChar2)
    _unbind(panel.text_ville, wx.EVT_KILL_FOCUS, panel.Ville_KillFocus2)
    _unbind(panel.text_cp, wx.EVT_KILL_FOCUS, panel.Code_KillFocus2)
    panel.text_ville.Bind(wx.EVT_TEXT, panel.OnTextVille)
    panel.text_cp.Bind(wx.EVT_TEXT, panel.OnTextCP)

    # Naissance : conserver l'assistance locale pour la France, mais ne jamais
    # forcer une ville étrangère à exister dans Villes.db3.
    _unbind(panel.text_ville_naiss, wx.EVT_TEXT, panel.VilleText1)
    _unbind(panel.text_ville_naiss, wx.EVT_CHAR, panel.VilleChar1)
    _unbind(panel.text_ville_naiss, wx.EVT_KILL_FOCUS, panel.Ville_KillFocus1)
    _unbind(panel.text_cp_naiss, wx.EVT_KILL_FOCUS, panel.Code_KillFocus1)

    def on_birth_text(event):
        if _country_is_france(panel):
            panel.VilleText1(event)
        else:
            panel.MaJ_DateNaiss_Fiche()
            event.Skip()

    def on_birth_char(event):
        if _country_is_france(panel):
            panel.VilleChar1(event)
        else:
            event.Skip()

    def on_birth_city_kill(event):
        if _country_is_france(panel):
            panel.Ville_KillFocus1(event)
        else:
            panel.MaJ_DateNaiss_Fiche()
            panel.MAJ_barre_problemes()
            event.Skip()

    def on_birth_cp_kill(event):
        if _country_is_france(panel):
            panel.Code_KillFocus1(event)
        else:
            panel.MaJ_DateNaiss_Fiche()
            panel.MAJ_barre_problemes()
            event.Skip()

    # Conserver les closures en attributs évite leur collecte et facilite un
    # éventuel démontage ultérieur.
    panel._tw_birth_text = on_birth_text
    panel._tw_birth_char = on_birth_char
    panel._tw_birth_city_kill = on_birth_city_kill
    panel._tw_birth_cp_kill = on_birth_cp_kill

    panel.text_ville_naiss.Bind(wx.EVT_TEXT, on_birth_text)
    panel.text_ville_naiss.Bind(wx.EVT_CHAR, on_birth_char)
    panel.text_ville_naiss.Bind(wx.EVT_KILL_FOCUS, on_birth_city_kill)
    panel.text_cp_naiss.Bind(wx.EVT_KILL_FOCUS, on_birth_cp_kill)
