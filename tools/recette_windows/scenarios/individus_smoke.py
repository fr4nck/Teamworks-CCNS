from __future__ import annotations

import json
import time

from ..errors import RecipeError


def _write_keyboard(driver, trace):
    (driver.artifacts_dir / "keyboard-focus.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _focus_label(snapshot):
    name = snapshot.get("name") or "<sans nom>"
    control_type = snapshot.get("control_type") or "<type inconnu>"
    handle = snapshot.get("handle")
    return "%s [%s] hwnd=%r" % (name, control_type, handle)


def _record_keyboard(driver, trace, control, key, sender, expected, expect_focus_change=None):
    try:
        control.set_focus()
    except Exception:
        pass
    time.sleep(0.1)
    before = driver.focus_snapshot()
    sender()
    time.sleep(0.2)
    after = driver.focus_snapshot()
    focus_changed = before != after

    if expect_focus_change is None:
        result = "OBSERVÉ"
    else:
        result = "OK" if focus_changed == expect_focus_change else "KO"

    record = {
        "start": before,
        "key": key,
        "received": after,
        "expected": expected,
        "obtained": "focus avant: %s ; focus après: %s"
        % (_focus_label(before), _focus_label(after)),
        "focus_changed": focus_changed,
        "result": result,
    }
    trace.append(record)
    _write_keyboard(driver, trace)
    return record


def _wait_person_list(driver, main, timeout=None):
    deadline = time.monotonic() + (driver.timeout if timeout is None else float(timeout))
    while time.monotonic() < deadline:
        try:
            return driver.find_list("OL_personnes", window=main)
        except LookupError:
            time.sleep(0.1)
    raise RecipeError("La page Individus n'a pas expose la liste OL_personnes")


def run(driver):
    """Main -> Individus -> fiche (si ligne) ou Options -> fermeture -> main."""
    main = driver.wait_main_window()
    keyboard = []
    _write_keyboard(driver, keyboard)

    nav = driver.find_named("Individus", window=main)
    _record_keyboard(
        driver,
        keyboard,
        nav,
        "TAB",
        lambda: driver.send_tab(reverse=False),
        "le focus quitte le bouton Individus vers le controle focusable suivant",
        expect_focus_change=True,
    )
    _record_keyboard(
        driver,
        keyboard,
        nav,
        "Shift+TAB",
        lambda: driver.send_tab(reverse=True),
        "le focus quitte le bouton Individus vers le controle focusable precedent",
        expect_focus_change=True,
    )
    enter_record = _record_keyboard(
        driver,
        keyboard,
        nav,
        "ENTER",
        driver.send_enter,
        "Entree active Individus sans sauvegarde ni operation destructive",
    )
    try:
        _wait_person_list(driver, main, timeout=min(driver.timeout, 3.0))
        enter_record["result"] = "OK"
        enter_record["obtained"] += " ; la liste Individus est visible"
    except RecipeError:
        enter_record["result"] = "KO"
        enter_record["obtained"] += " ; la liste Individus n'est pas devenue visible"
    _write_keyboard(driver, keyboard)

    # Le parcours fonctionnel conserve un clic souris reel, independamment du test clavier.
    driver.click_named("Individus", window=main)
    list_control = _wait_person_list(driver, main)

    driver.assert_responsive(main)
    items = driver.list_items(list_control)
    if items:
        before = driver.window_handles()
        driver.double_click_list_item(list_control, index=0)
        dialog = driver.wait_new_window(before)
        action = "double-clic premiere fiche"
    else:
        before = driver.open_context_menu_item(list_control, "Options")
        dialog = driver.wait_new_window(before)
        action = "Options de liste (liste sans item UIA exploitable)"

    driver.assert_responsive(dialog)
    dialog_focus_before_escape = driver.focus_snapshot(dialog)
    dialog_handle = int(dialog.handle)
    close_method = driver.close_dialog(dialog)
    escape_record = {
        "start": dialog_focus_before_escape,
        "key": "ESC",
        "received": driver.focus_snapshot(main),
        "expected": "le dialogue se ferme par Echap et le focus revient dans la fenetre principale",
        "obtained": "fermeture=%s ; focus apres: %s"
        % (close_method, _focus_label(driver.focus_snapshot(main))),
        "dialog_closed": dialog_handle not in driver.window_handles(),
        "result": "OK" if close_method == "escape" else "KO",
    }
    keyboard.append(escape_record)
    _write_keyboard(driver, keyboard)

    driver.assert_responsive(main)
    keyboard_failures = [entry["key"] for entry in keyboard if entry.get("result") == "KO"]
    if keyboard_failures:
        raise RecipeError("Tests clavier KO: %s" % ", ".join(keyboard_failures))

    return {
        "scenario": "individus-smoke",
        "action": action,
        "main_hwnd": int(main.handle),
        "dialog_closed": True,
        "returned_to_main": True,
        "keyboard": keyboard,
    }
