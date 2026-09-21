from pathlib import Path
import re


ROOT = Path("teamworks")
UI_ROOTS = (ROOT / "Ctrl", ROOT / "Dlg")
EXTRA = (ROOT / "Gadget.py", ROOT / "Teamworks.py", ROOT / "Teamworks_core.py")

BUTTON_ASSIGN_RE = re.compile(
    r"self\.(?P<name>\w+)\s*=\s*"
    r"(?:wx\.(?:Button|BitmapButton|ToggleButton)|"
    r"CTRL_Bouton_image\.(?:CTRL|Toggle))\s*\(",
    re.MULTILINE,
)
DEFAULT_WRAP_RE = re.compile(
    r"wx\.WrapSizer\(\s*wx\.HORIZONTAL\s*\)",
    re.MULTILINE,
)
NATIVE_BUTTON_RE = re.compile(
    r"wx\.(?:Button|BitmapButton|ToggleButton)\s*\(",
    re.MULTILINE,
)


def _production_source(path):
    source = path.read_text(encoding="utf-8")
    # Les harnais manuels sous __main__ ne font pas partie de l'interface livrée.
    marker = re.search(
        r"^\s*if\s+__name__\s*==\s*['\"]__main__['\"]\s*:",
        source,
        re.MULTILINE,
    )
    return source[: marker.start()] if marker else source


def _ui_files():
    files = []
    for base in UI_ROOTS:
        files.extend(base.rglob("*.py"))
    files.extend(EXTRA)
    return sorted(set(files))


def test_aucun_wrapsizer_action_n_utilise_le_drapeau_extensible_par_defaut():
    violations = []
    for path in _ui_files():
        source = _production_source(path)
        for match in DEFAULT_WRAP_RE.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            violations.append(f"{path}:{line}")

    assert not violations, (
        "wx.WrapSizer(wx.HORIZONTAL) active EXTEND_LAST_ON_EACH_LINE et peut "
        "transformer le dernier bouton en barre géante. Utiliser un second "
        "argument explicite (0 ou REMOVE_LEADING_SPACES).\n"
        + "\n".join(violations)
    )


def test_aucun_bouton_action_n_est_explicitement_etire_sans_justification():
    violations = []
    for path in _ui_files():
        source = _production_source(path)
        names = {m.group("name") for m in BUTTON_ASSIGN_RE.finditer(source)}
        if not names:
            continue

        lines = source.splitlines()
        for name in names:
            pattern = re.compile(
                r"\.Add\(\s*self\." + re.escape(name)
                + r"\s*,[^\n]*wx\.EXPAND[^\n]*\)"
            )
            for match in pattern.finditer(source):
                lineno = source.count("\n", 0, match.start()) + 1
                line = lines[lineno - 1]
                if "button-stretch-ok:" in line:
                    continue
                violations.append(f"{path}:{lineno}: {line.strip()}")

    assert not violations, (
        "Un bouton d'action ne doit pas absorber l'espace disponible. "
        "Retirer wx.EXPAND ou documenter un vrai sélecteur extensible avec "
        "'# button-stretch-ok: raison'.\n"
        + "\n".join(violations)
    )


def test_aucun_bouton_wx_natif_ne_reste_dans_interface_livree():
    violations = []
    for path in _ui_files():
        if path.name == "CTRL_Bouton_image.py":
            continue
        source = _production_source(path)
        lines = source.splitlines()
        for match in NATIVE_BUTTON_RE.finditer(source):
            lineno = source.count("\n", 0, match.start()) + 1
            index = lineno - 1
            violations.append(f"{path}:{lineno}: {lines[index].strip()}")

    assert not violations, (
        "Tous les boutons de l'interface livrée doivent passer par "
        "CTRL_Bouton_image (CTRL, Compact ou Toggle). Aucun wx.Button, "
        "wx.BitmapButton ou wx.ToggleButton natif ne doit subsister.\n"
        + "\n".join(violations)
    )
