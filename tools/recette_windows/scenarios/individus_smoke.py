from __future__ import annotations

import time

from ..errors import RecipeError


def _record_keyboard(driver, trace, control, key, sender, expected):
    try:
        control.set_focus()
    except Exception:
        pass
    time.sleep(0.1)
    before = driver.focus_snapshot()
    sender()
    time.sleep(0.2)
    after = driver.focus_snapshot()
    trace.append(
        {
            "start": before,
            "key": key,
            "received": after,
            "expected": expected,
            "focus_changed": before != after,
        }
    )
    return after


def run(driver):
    """Main -> Individus -> fiche (si ligne) ou Options -> fermeture -> main."""
    main = driver.wait_main_window()
    keyboard = []

    nav = driver.find_named("Individus", window=main)
    _record_keyboard(
        driver,
        keyboard,
        nav,
        "TAB",
        lambda: driver.send_tab(reverse=False),
        "le focus quitte le bouton Individus vers le controle focusable suivant",
    )
    _record_keyboard(
        driver,
        keyboard,
        nav,
        "Shift+TAB",
        lambda: driver.send_tab(reverse=True),
        "le focus quitte le bouton Individus vers le controle focusable precedent",
    )
    _record_keyboard(
        driver,
        keyboard,
        nav,
        "ENTER",
        driver.send_enter,
        "le bouton Individus traite Entree sans sauvegarde ni operation destructive",
    )

    # Le parcours fonctionnel conserve un clic souris reel, independamment du test clavier.
    driver.click_named("Individus", window=main)

    deadline = time.monotonic() + driver.timeout
    list_control = None
    while time.monotonic() < deadline:
        try:
            list_control = driver.find_list("OL_personnes", window=main)
            break
        except LookupError:
            time.sleep(0.1)
    if list_control is None:
        raise RecipeError("La page Individus n'a pas expose la liste OL_personnes")

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
    driver.close_dialog(dialog)
    keyboard.append(
        {
            "start": dialog_focus_before_escape,
            "key": "ESC",
            "received": driver.focus_snapshot(main),
            "expected": "le dialogue se ferme et le focus revient dans la fenetre principale",
            "dialog_closed": dialog_handle not in driver.window_handles(),
        }
    )
    driver.assert_responsive(main)
    return {
        "scenario": "individus-smoke",
        "action": action,
        "main_hwnd": int(main.handle),
        "dialog_closed": True,
        "returned_to_main": True,
        "keyboard": keyboard,
    }
