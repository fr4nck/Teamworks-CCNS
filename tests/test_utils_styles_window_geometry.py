import importlib.util
import sys
import types
from pathlib import Path

import pytest


STYLES_PATH = Path("teamworks/Utils/UTILS_Styles.py")


class FakeRect:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def GetWidth(self):
        return self.width

    def GetHeight(self):
        return self.height


class FakeWindow:
    def __init__(self, display_index=0):
        self.display_index = display_index
        self.size = None
        self.min_size = None
        self.centred = False

    def SetSize(self, size):
        self.size = size

    def SetMinSize(self, size):
        self.min_size = size

    def CentreOnParent(self):
        self.centred = True


@pytest.fixture
def styles(monkeypatch):
    fake_wx = types.ModuleType("wx")
    fake_wx.FONTWEIGHT_BOLD = 700
    fake_wx.FONTWEIGHT_NORMAL = 400
    fake_wx.NOT_FOUND = -1
    fake_wx.display_size = (1280, 800)

    class Display:
        areas = {0: (1920, 1040)}
        fail_client_area = False

        @staticmethod
        def GetFromWindow(window):
            return window.display_index

        def __init__(self, index):
            self.index = index

        def IsOk(self):
            return self.index in self.areas

        def GetClientArea(self):
            if self.fail_client_area:
                raise RuntimeError("client area unavailable")
            width, height = self.areas[self.index]
            return FakeRect(width, height)

    fake_wx.Display = Display
    fake_wx.GetDisplaySize = lambda: fake_wx.display_size

    utils_package = types.ModuleType("Utils")
    utils_package.__path__ = []
    customize = types.ModuleType("UTILS_Customize")
    interface = types.ModuleType("UTILS_Interface")
    interface.INTERFACE_SCALE_MIN = 75
    interface.INTERFACE_SCALE_MAX = 200
    interface.INTERFACE_SCALE_DEFAULT = 100
    customize.GetValeur = lambda *args, **kwargs: 100
    utils_package.UTILS_Customize = customize
    utils_package.UTILS_Interface = interface

    monkeypatch.setitem(sys.modules, "wx", fake_wx)
    monkeypatch.setitem(sys.modules, "Utils", utils_package)
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Customize", customize)
    monkeypatch.setitem(sys.modules, "Utils.UTILS_Interface", interface)

    spec = importlib.util.spec_from_file_location("test_utils_styles_geometry", STYLES_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "Scale", lambda value, minimum=1: max(minimum, int(value)))
    return module


def test_size_is_unchanged_when_work_area_is_larger(styles):
    assert styles.GetWindowSize("standard", display_size=(1920, 1080)) == (1075, 691)


def test_width_is_clamped_to_work_area(styles):
    assert styles.GetWindowSize("standard", display_size=(500, 1000)) == (500, 640)


def test_height_is_clamped_to_work_area(styles):
    assert styles.GetWindowSize("standard", display_size=(2000, 400)) == (1120, 400)


def test_width_and_height_are_clamped_to_work_area(styles):
    assert styles.GetWindowSize("standard", display_size=(500, 400)) == (500, 400)


def test_apply_profile_clamps_minimum_and_uses_window_display(styles):
    styles.wx.Display.areas = {0: (1920, 1040), 1: (700, 500)}
    window = FakeWindow(display_index=1)

    assert styles.ApplyWindowProfile(window, "workspace", centre=False) == (700, 500)
    assert window.size == (700, 500)
    assert window.min_size == (700, 500)
    assert window._teamworks_window_profile == "workspace"


@pytest.mark.parametrize("profile", ["compact", "standard", "wide", "workspace"])
def test_profiles_fit_a_small_work_area(styles, profile):
    assert styles.GetWindowSize(profile, display_size=(320, 240)) == (320, 240)


def test_display_client_area_falls_back_to_screen_size(styles):
    styles.wx.Display.fail_client_area = True
    styles.wx.display_size = (1280, 800)

    assert styles.GetWindowSize("standard", window=FakeWindow()) == (717, 512)


def test_missing_display_api_falls_back_to_screen_size(styles):
    del styles.wx.Display
    styles.wx.display_size = (1024, 768)

    assert styles.GetWindowSize("compact", window=FakeWindow()) == (420, 338)
