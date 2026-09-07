from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

from .errors import RecipeError, UnsupportedRunner
from .guards import assert_not_destructive, assert_not_destructive_confirmation
from .selectors import element_control_type, element_name, find_named

WM_NULL = 0x0000
SMTO_ABORTIFHUNG = 0x0002


class WindowsRecipeDriver:
    """Pilote externe: uniquement UI Automation, souris et clavier Windows."""

    def __init__(self, root, artifacts_dir, timeout=20.0, backend="uia"):
        self.root = Path(root).resolve()
        self.artifacts_dir = Path(artifacts_dir).resolve()
        self.timeout = float(timeout)
        self.backend = backend
        self.process = None
        self.main_window = None
        self._stdout = None
        self._stderr = None
        self._Desktop = None
        self._Application = None
        self._send_keys = None
        self.started_at = None
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def require_windows_interactive():
        if platform.system() != "Windows":
            raise UnsupportedRunner(
                "La recette UI exige Windows avec une session bureau interactive; runner actuel: %s"
                % platform.platform()
            )
        if not os.environ.get("SESSIONNAME"):
            raise UnsupportedRunner(
                "SESSIONNAME est absent: impossible de confirmer une session Windows interactive."
            )

    def _load_pywinauto(self):
        try:
            from pywinauto import Application, Desktop
            from pywinauto.keyboard import send_keys
        except ImportError as exc:
            raise UnsupportedRunner(
                "pywinauto manque. Installer requirements/recette-windows.txt."
            ) from exc
        self._Application = Application
        self._Desktop = Desktop
        self._send_keys = send_keys

    def start(self):
        self.require_windows_interactive()
        self._load_pywinauto()
        launcher = self.root / "run_teamworks.py"
        if not launcher.is_file():
            raise RecipeError("Lanceur introuvable: %s" % launcher)

        self.started_at = time.time()
        self._stdout = (self.artifacts_dir / "stdout.log").open("w", encoding="utf-8", errors="replace")
        self._stderr = (self.artifacts_dir / "stderr.log").open("w", encoding="utf-8", errors="replace")
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        self.process = subprocess.Popen(
            [sys.executable, str(launcher)],
            cwd=str(self.root),
            stdout=self._stdout,
            stderr=self._stderr,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        return self.process.pid

    def wait_main_window(self, title_re=r"^Teamworks - .+"):
        self._ensure_process_alive("attente de la fenetre principale")
        app = self._Application(backend=self.backend).connect(process=self.process.pid, timeout=self.timeout)
        spec = app.window(title_re=title_re)
        spec.wait("exists visible enabled ready", timeout=self.timeout)
        self.main_window = spec.wrapper_object()
        self.assert_responsive(self.main_window)
        return self.main_window

    def descendants(self, window=None):
        target = window or self.main_window
        if target is None:
            raise RecipeError("Fenetre principale non initialisee")
        return target.descendants()

    def find_named(self, name, window=None, control_types=()):
        return find_named(self.descendants(window), name, control_types=control_types)

    def find_list(self, name="OL_personnes", window=None):
        target = window or self.main_window
        try:
            return self.find_named(name, window=target)
        except LookupError:
            pass

        candidates = []
        for element in self.descendants(target):
            control_type = element_control_type(element).casefold()
            info = getattr(element, "element_info", None)
            class_name = str(getattr(info, "class_name", "") or "").casefold()
            if control_type not in ("list", "datagrid") and "syslistview32" not in class_name:
                continue
            try:
                if not (element.is_visible() and element.is_enabled()):
                    continue
                rectangle = element.rectangle()
                area = max(0, rectangle.width()) * max(0, rectangle.height())
            except Exception:
                area = 0
            candidates.append((area, element))
        if not candidates:
            raise LookupError("Aucune liste native/UIA exploitable trouvee pour %r" % name)
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return candidates[0][1]

    def click_named(self, name, window=None, control_types=()):
        control = self.find_named(name, window=window, control_types=control_types)
        assert_not_destructive([element_name(control)], context="controle clique")
        control.click_input()
        return control

    def select_list_item(self, list_control, index=0):
        items = self.list_items(list_control)
        if index < 0 or index >= len(items):
            raise RecipeError("Element de liste %d indisponible (taille=%d)" % (index, len(items)))
        item = items[index]
        try:
            item.select()
        except Exception:
            item.click_input()
        return item

    def double_click_list_item(self, list_control, index=0):
        item = self.select_list_item(list_control, index=index)
        item.double_click_input()
        return item

    def list_items(self, list_control):
        candidates = []
        try:
            candidates.extend(list_control.descendants(control_type="DataItem"))
        except Exception:
            pass
        try:
            candidates.extend(list_control.descendants(control_type="ListItem"))
        except Exception:
            pass
        unique = []
        seen = set()
        for item in candidates:
            key = getattr(item, "handle", None) or id(item)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def send_tab(self, reverse=False):
        self._guard_foreground()
        self._send_keys("+{TAB}" if reverse else "{TAB}")

    def send_enter(self):
        self._guard_foreground()
        self._send_keys("{ENTER}")

    def send_escape(self):
        self._send_keys("{ESC}")

    def window_handles(self):
        if not self.process:
            return set()
        return {
            int(window.handle)
            for window in self._Desktop(backend=self.backend).windows(
                process=self.process.pid, visible_only=True
            )
        }

    def wait_new_window(self, previous_handles, timeout=None):
        deadline = time.monotonic() + (self.timeout if timeout is None else float(timeout))
        while time.monotonic() < deadline:
            self._ensure_process_alive("attente d'un dialogue")
            windows = self._Desktop(backend=self.backend).windows(
                process=self.process.pid, visible_only=True
            )
            for window in windows:
                if int(window.handle) not in previous_handles:
                    self.guard_window(window)
                    self.assert_responsive(window)
                    return window
            time.sleep(0.1)
        raise RecipeError("Aucun nouveau dialogue detecte dans le delai imparti")

    def guard_window(self, window):
        texts = [element_name(window)]
        try:
            texts.extend(element_name(child) for child in window.descendants())
        except Exception:
            pass
        assert_not_destructive_confirmation(texts, context="dialogue")

    def assert_responsive(self, window, timeout_ms=1500):
        handle = int(window.handle)
        result = ctypes.c_size_t()
        send_message_timeout = ctypes.windll.user32.SendMessageTimeoutW
        send_message_timeout.argtypes = (
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
            wintypes.UINT,
            wintypes.UINT,
            ctypes.POINTER(ctypes.c_size_t),
        )
        send_message_timeout.restype = wintypes.LPARAM
        ok = send_message_timeout(
            handle,
            WM_NULL,
            0,
            0,
            SMTO_ABORTIFHUNG,
            int(timeout_ms),
            ctypes.byref(result),
        )
        if not ok:
            raise RecipeError("Fenetre non responsive (HWND=%s)" % handle)
        return True

    def close_dialog(self, window, timeout=5.0):
        handle = int(window.handle)
        self.guard_window(window)
        try:
            window.set_focus()
        except Exception:
            pass
        self.send_escape()
        if self._wait_handle_gone(handle, timeout):
            return
        window.close()
        if not self._wait_handle_gone(handle, timeout):
            raise RecipeError("Le dialogue HWND=%s ne se ferme ni par Echap ni par WM_CLOSE" % handle)

    def open_context_menu_item(self, control, item_name):
        before = self.window_handles()
        control.right_click_input()
        deadline = time.monotonic() + min(self.timeout, 5.0)
        while time.monotonic() < deadline:
            try:
                elements = self._Desktop(backend=self.backend).windows(visible_only=True)
                for top in reversed(elements):
                    info = getattr(top, "element_info", None)
                    process_id = getattr(info, "process_id", None) if info else None
                    if process_id not in (None, self.process.pid):
                        continue
                    try:
                        match = find_named(top.descendants(), item_name)
                    except LookupError:
                        continue
                    assert_not_destructive([item_name], context="menu contextuel")
                    match.click_input()
                    return before
            except Exception:
                pass
            time.sleep(0.1)
        raise RecipeError("Entree de menu contextuel introuvable: %s" % item_name)

    def capture_failure(self, exc):
        (self.artifacts_dir / "failure.txt").write_text(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            encoding="utf-8",
        )
        self.dump_windows()
        try:
            window = self._foreground_own_window() or self.main_window
            if window is not None:
                image = window.capture_as_image()
                image.save(self.artifacts_dir / "failure.png")
        except Exception as screenshot_exc:
            (self.artifacts_dir / "screenshot-error.txt").write_text(
                repr(screenshot_exc), encoding="utf-8"
            )

    def dump_windows(self):
        rows = []
        if self._Desktop is None or self.process is None:
            return
        try:
            tops = self._Desktop(backend=self.backend).windows(
                process=self.process.pid, visible_only=False
            )
        except Exception:
            tops = []
        for top in tops:
            rows.append(self._describe_element(top, depth=0))
            try:
                rows.extend(self._describe_element(child, depth=1) for child in top.descendants())
            except Exception as exc:
                rows.append("  <descendants error: %r>" % exc)
        (self.artifacts_dir / "windows.txt").write_text("\n".join(rows), encoding="utf-8")

    def collect_logs(self):
        if self.started_at is None:
            return
        destination = self.artifacts_dir / "app-logs"
        copied = 0
        for folder in ("Temp", "Logs", "logs", "teamworks/Temp", "teamworks/Logs"):
            base = self.root / folder
            if not base.is_dir():
                continue
            for path in base.glob("*.log"):
                try:
                    if path.stat().st_mtime + 1 < self.started_at:
                        continue
                    destination.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination / path.name)
                    copied += 1
                except OSError:
                    pass
        return copied

    def shutdown(self, graceful=True):
        exit_code = None
        try:
            if self.process and self.process.poll() is None and graceful and self.main_window is not None:
                try:
                    self.main_window.set_focus()
                    self._send_keys("%{F4}")
                    self.process.wait(timeout=8)
                except Exception:
                    pass
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            if self.process:
                exit_code = self.process.poll()
        finally:
            if self._stdout:
                self._stdout.flush()
                self._stdout.close()
                self._stdout = None
            if self._stderr:
                self._stderr.flush()
                self._stderr.close()
                self._stderr = None
            self.collect_logs()
            (self.artifacts_dir / "process.json").write_text(
                json.dumps(
                    {
                        "pid": self.process.pid if self.process else None,
                        "exit_code": exit_code,
                        "backend": self.backend,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        return exit_code

    def _guard_foreground(self):
        window = self._foreground_own_window()
        if window is not None:
            self.guard_window(window)

    def _foreground_own_window(self):
        if self._Desktop is None or self.process is None:
            return None
        try:
            windows = self._Desktop(backend=self.backend).windows(
                process=self.process.pid, visible_only=True, active_only=True
            )
            return windows[0] if windows else None
        except Exception:
            return None

    def _wait_handle_gone(self, handle, timeout):
        deadline = time.monotonic() + float(timeout)
        while time.monotonic() < deadline:
            if handle not in self.window_handles():
                return True
            time.sleep(0.1)
        return False

    def _ensure_process_alive(self, context):
        if self.process is None:
            raise RecipeError("Application non lancee")
        code = self.process.poll()
        if code is not None:
            raise RecipeError("Application terminee (code=%s) pendant %s" % (code, context))

    @staticmethod
    def _describe_element(element, depth):
        info = getattr(element, "element_info", None)
        return "%sname=%r type=%r class=%r auto_id=%r handle=%r" % (
            "  " * depth,
            element_name(element),
            element_control_type(element),
            getattr(info, "class_name", "") if info else "",
            getattr(info, "automation_id", "") if info else "",
            getattr(element, "handle", None),
        )
