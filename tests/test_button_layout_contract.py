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
    return source.split('if __name__ == "__main__":', 1)[0].split(
        "if __name__ == '__main__':", 1
    )[0]


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

        for lineno, line in enumerate(source.splitlines(), 1):
            if "button-stretch-ok:" in line:
                continue
            if "wx.EXPAND" not in line or ".Add(" not in line:
                continue
            for name in names:
                if f"self.{name}" in line:
                    violations.append(f"{path}:{lineno}: {line.strip()}")
                    break

    assert not violations, (
        "Un bouton d'action ne doit pas absorber l'espace disponible. "
        "Retirer wx.EXPAND ou documenter un vrai sélecteur extensible avec "
        "'# button-stretch-ok: raison'.\n"
        + "\n".join(violations)
    )


def test_boutons_actions_standards_utilisent_le_controle_commun():
    violations = []
    for path in _ui_files():
        source = _production_source(path)
        lines = source.splitlines()
        for match in NATIVE_BUTTON_RE.finditer(source):
            lineno = source.count("\n", 0, match.start()) + 1
            index = lineno - 1
            contexte = "\n".join(lines[max(0, index - 2): index + 1])
            if "native-button-ok:" in contexte:
                continue
            violations.append(f"{path}:{lineno}: {lines[index].strip()}")

    assert not violations, (
        "Les boutons d'action utilisateur doivent passer par "
        "CTRL_Bouton_image. Les rares contrôles natifs réellement techniques "
        "doivent porter '# native-button-ok: raison'.\n"
        + "\n".join(violations)
    )
