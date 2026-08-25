#!/usr/bin/env python3
"""Qualifie l'écran de configuration d'expéditeur Windows sans réseau ni écriture BDD."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_sender_config_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_sender_config_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "sender-config-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_SENDER_CONFIG_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_SENDER_CONFIG_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_dialog = None
            try:
                print("TEAMWORKS_SMOKE_SENDER_CONFIG_STAGE:imports", flush=True)
                from Dlg import DLG_Saisie_email_exp as _smoke_sender
                from Utils import UTILS_Mailing as _smoke_mailing

                print("TEAMWORKS_SMOKE_SENDER_CONFIG_STAGE:dialog", flush=True)
                _smoke_dialog = _smoke_sender.Dialog(frame, IDadresse=None)
                _smoke_dialog.Show()
                wx.Yield()
                assert _smoke_dialog.GetClientSize().GetWidth() > 0
                assert _smoke_dialog.GetClientSize().GetHeight() > 0

                _smoke_messages = []
                _smoke_original_message_dialog = wx.MessageDialog

                class _SmokeMessageDialog:
                    def __init__(self, parent, message, caption, style=0, *args, **kwargs):
                        _smoke_messages.append(str(message))

                    def ShowModal(self):
                        return wx.ID_OK

                    def Destroy(self):
                        return None

                wx.MessageDialog = _SmokeMessageDialog
                try:
                    print("TEAMWORKS_SMOKE_SENDER_CONFIG_STAGE:mailjet-legacy", flush=True)
                    _smoke_mailjet = _smoke_dialog.GetPage("mailjet")
                    _smoke_mailjet.SetDonnees({
                        "adresse": " Direction@Example.Technology ",
                        "nom_adresse": "PMSL",
                        "parametres": "api_key==key==suffix##fragment-corrompu##api_secret==secret==suffix",
                    })
                    assert _smoke_mailjet.ctrl_api_key.GetValue() == "key==suffix"
                    assert _smoke_mailjet.ctrl_api_secret.GetValue() == "secret==suffix"
                    _smoke_mailjet_data = _smoke_mailjet.GetDonnees()
                    assert _smoke_mailjet_data["adresse"] == "Direction@example.technology"
                    assert _smoke_mailing.ParseBackendParameters(
                        _smoke_mailjet_data["parametres"], strict=True
                    ) == {
                        "api_key": "key==suffix",
                        "api_secret": "secret==suffix",
                    }
                    assert _smoke_mailjet.Validation() is True

                    print("TEAMWORKS_SMOKE_SENDER_CONFIG_STAGE:mailjet-invalid-address", flush=True)
                    _smoke_messages[:] = []
                    _smoke_mailjet.ctrl_adresse.SetValue("adresse-invalide")
                    assert _smoke_mailjet.Validation() is False
                    assert any("Adresse d'expédition invalide" in text for text in _smoke_messages)

                    print("TEAMWORKS_SMOKE_SENDER_CONFIG_STAGE:smtp-port", flush=True)
                    _smoke_smtp = _smoke_dialog.GetPage("smtp")
                    _smoke_smtp.radio_predefini.SetValue(False)
                    _smoke_smtp.radio_personnalise.SetValue(True)
                    _smoke_smtp.OnRadioServeur(None)
                    _smoke_smtp.ctrl_adresse.SetValue(" Direction@Example.Technology ")
                    _smoke_smtp.ctrl_smtp.SetValue(" smtp.example.test ")
                    _smoke_smtp.ctrl_port.SetValue("70000")
                    _smoke_smtp.ctrl_authentification.SetValue(False)
                    _smoke_smtp.ctrl_startTLS.SetValue(True)
                    _smoke_smtp.OnRadioServeur(None)
                    _smoke_messages[:] = []
                    assert _smoke_smtp.Validation() is False
                    assert any("Port SMTP hors plage" in text for text in _smoke_messages)

                    _smoke_smtp.ctrl_port.SetValue("587")
                    _smoke_messages[:] = []
                    assert _smoke_smtp.Validation() is True
                    _smoke_smtp_data = _smoke_smtp.GetDonnees()
                    assert _smoke_smtp_data["adresse"] == "Direction@example.technology"
                    assert _smoke_smtp_data["smtp"] == "smtp.example.test"
                    assert _smoke_smtp_data["port"] == 587
                    assert _smoke_smtp_data["startTLS"] == 1
                finally:
                    wx.MessageDialog = _smoke_original_message_dialog

                _smoke_dialog.Destroy()
                _smoke_dialog = None
                wx.Yield()
                print("TEAMWORKS_SMOKE_SENDER_CONFIG_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_SENDER_CONFIG_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_dialog is not None:
                        _smoke_dialog.Destroy()
                except Exception:
                    pass
'''


def build_patched_entrypoint() -> int:
    core_source = CORE_SOURCE.read_text(encoding="utf-8")
    marker_count = core_source.count(MARKER_LINE)
    if marker_count < 1:
        raise RuntimeError(f"marqueur principal introuvable: count={marker_count}")
    patched_core_source = core_source.replace(MARKER_LINE, INJECTION, 1)
    if READY_MARKER not in patched_core_source or FAILURE_MARKER not in patched_core_source:
        raise RuntimeError("injection des marqueurs configuration expéditeur absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_sender_config_smoke as CORE"
    if import_line not in entrypoint_source:
        raise RuntimeError("import du cœur Teamworks introuvable dans la coque active")
    patched_entrypoint = entrypoint_source.replace(import_line, patched_import, 1)
    compile(patched_entrypoint, str(PATCHED), "exec")
    PATCHED.write_text(patched_entrypoint, encoding="utf-8")
    return marker_count


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    marker_count: int | None = None
    try:
        marker_count = build_patched_entrypoint()
        return_code, output = run_entrypoint(
            PATCHED,
            root=ROOT,
            teamworks_dir=TEAMWORKS_DIR,
            timeout=180,
        )
        write_diagnostic(
            REPORT,
            return_code=return_code,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        if STATICBOX_PARENT_WARNING in output:
            github_error_summary("Sender config StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Sender config smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Sender config smoke failed", output)
            print("marqueur configuration expéditeur absent", file=sys.stderr)
            return 2
        return 0
    except Exception:
        output = traceback.format_exc()
        write_diagnostic(
            REPORT,
            return_code=3,
            marker_count=marker_count,
            ready_marker=READY_MARKER,
            failure_marker=FAILURE_MARKER,
            output=output,
        )
        github_error_summary("Sender config smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
