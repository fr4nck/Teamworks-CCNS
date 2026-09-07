from __future__ import annotations

import time

from ..errors import RecipeError


def run(driver):
    """Main -> Individus -> fiche (si ligne) ou Options -> fermeture -> main."""
    main = driver.wait_main_window()
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
    driver.close_dialog(dialog)
    driver.assert_responsive(main)
    return {
        "scenario": "individus-smoke",
        "action": action,
        "main_hwnd": int(main.handle),
        "dialog_closed": True,
        "returned_to_main": True,
    }
