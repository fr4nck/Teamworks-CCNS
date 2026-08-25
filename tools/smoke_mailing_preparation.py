#!/usr/bin/env python3
"""Qualifie l'éditeur de mailing Windows sans effectuer d'envoi réseau."""

from __future__ import annotations

from pathlib import Path
import sys
import traceback

from smoke_runtime import github_error_summary, run_entrypoint, write_diagnostic

ROOT = Path(__file__).resolve().parents[1]
TEAMWORKS_DIR = ROOT / "teamworks"
ENTRYPOINT_SOURCE = TEAMWORKS_DIR / "Teamworks.py"
CORE_SOURCE = TEAMWORKS_DIR / "Teamworks_core.py"
PATCHED = TEAMWORKS_DIR / "Teamworks_mailing_preparation_smoke.py"
PATCHED_CORE = TEAMWORKS_DIR / "Teamworks_core_mailing_preparation_smoke.py"
REPORT_DIR = ROOT / "artifacts" / "mailing-preparation-smoke"
REPORT = REPORT_DIR / "diagnostic.txt"
MARKER_LINE = '            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)'
READY_MARKER = "TEAMWORKS_SMOKE_MAILING_PREPARATION_READY"
FAILURE_MARKER = "TEAMWORKS_SMOKE_MAILING_PREPARATION_FAILED"
STATICBOX_PARENT_WARNING = "of wxStaticBoxSizer should be created as child of its wxStaticBox"

INJECTION = r'''            print("TEAMWORKS_SMOKE_EXAMPLE_READY", flush=True)
            _smoke_tempdir = None
            try:
                print("TEAMWORKS_SMOKE_MAILING_STAGE:imports", flush=True)
                import tempfile as _smoke_tempfile
                from pathlib import Path as _smoke_Path
                from Dlg import DLG_Mailer as _smoke_mailer
                from Utils import UTILS_Envoi_email as _smoke_email

                print("TEAMWORKS_SMOKE_MAILING_STAGE:backend-factory", flush=True)
                _smoke_original_parametres = _smoke_email.UTILS_Parametres.Parametres
                _smoke_original_get_connection = _smoke_email.mail.get_connection
                _smoke_original_smtp_class = _smoke_email.smtplib.SMTP
                import mailjet_rest as _smoke_mailjet_rest
                _smoke_original_mailjet_client = _smoke_mailjet_rest.Client
                try:
                    _smoke_email.UTILS_Parametres.Parametres = lambda *args, **kwargs: None

                    _smoke_smtp_connections = []

                    class _SmokeSMTPConnection:
                        def __init__(self, **kwargs):
                            self.kwargs = kwargs
                            self.opened = False
                            self.closed = False

                        def open(self):
                            self.opened = True
                            return 1

                        def close(self):
                            self.closed = True

                    def _smoke_get_connection(**kwargs):
                        connection = _SmokeSMTPConnection(**kwargs)
                        _smoke_smtp_connections.append(connection)
                        return connection

                    _smoke_email.mail.get_connection = _smoke_get_connection
                    _smoke_smtp = _smoke_email.Messagerie(
                        backend=" SMTP ",
                        hote=" smtp.example.fr ",
                        port="587",
                        utilisateur="direction@example.fr",
                        motdepasse="secret",
                        email_exp=" Direction@PMSL.Association ",
                        nom_exp="PMSL",
                        timeout=20,
                        use_tls=1,
                        parametres=None,
                    )
                    assert isinstance(_smoke_smtp, _smoke_email.SmtpV2)
                    assert _smoke_smtp.hote == "smtp.example.fr"
                    assert _smoke_smtp.port == 587
                    assert _smoke_smtp.email_exp == "Direction@pmsl.association"
                    _smoke_smtp.Connecter()
                    assert len(_smoke_smtp_connections) == 1
                    assert _smoke_smtp_connections[0].opened is True
                    assert _smoke_smtp_connections[0].kwargs["host"] == "smtp.example.fr"
                    assert _smoke_smtp_connections[0].kwargs["port"] == 587
                    assert _smoke_smtp_connections[0].kwargs["username"] == "direction@example.fr"
                    assert _smoke_smtp_connections[0].kwargs["password"] == "secret"
                    assert _smoke_smtp_connections[0].kwargs["use_tls"] is True
                    _smoke_smtp.Fermer()
                    assert _smoke_smtp_connections[0].closed is True

                    _smoke_legacy_calls = []

                    class _SmokeLegacySMTP:
                        def __init__(self, *args, **kwargs):
                            _smoke_legacy_calls.append((args, kwargs))
                            self.closed = False

                        def close(self):
                            self.closed = True

                    _smoke_email.smtplib.SMTP = _SmokeLegacySMTP
                    _smoke_legacy = _smoke_email.Messagerie(
                        backend="smtp_obsolete",
                        hote="smtp.legacy.fr",
                        port=25,
                        utilisateur=None,
                        motdepasse=None,
                        email_exp="direction@example.fr",
                        nom_exp="PMSL",
                        timeout=10,
                        use_tls=False,
                        parametres=None,
                    )
                    assert isinstance(_smoke_legacy, _smoke_email.SmtpV1)
                    _smoke_legacy.Connecter()
                    assert len(_smoke_legacy_calls) == 1
                    assert _smoke_legacy_calls[0][0] == ("smtp.legacy.fr", 25)
                    assert _smoke_legacy_calls[0][1]["timeout"] == 10
                    _smoke_legacy.Fermer()

                    _smoke_mailjet_calls = []

                    class _SmokeMailjetClient:
                        def __init__(self, auth=None, version=None):
                            self.auth = auth
                            self.version = version
                            _smoke_mailjet_calls.append((auth, version))

                    _smoke_mailjet_rest.Client = _SmokeMailjetClient
                    _smoke_mailjet = _smoke_email.Messagerie(
                        backend=" MAILJET ",
                        hote=None,
                        port=None,
                        utilisateur=None,
                        motdepasse=None,
                        email_exp=" Direction@PMSL.Association ",
                        nom_exp="PMSL",
                        timeout=20,
                        use_tls=False,
                        parametres="api_key==public==part##api_secret==secret=value",
                    )
                    assert isinstance(_smoke_mailjet, _smoke_email.Mailjet)
                    assert _smoke_mailjet.dict_parametres == {
                        "api_key": "public==part",
                        "api_secret": "secret=value",
                    }
                    _smoke_mailjet.Connecter()
                    assert _smoke_mailjet_calls == [
                        (("public==part", "secret=value"), "v3.1")
                    ]

                    try:
                        _smoke_email.Messagerie(
                            backend="exchange",
                            hote="smtp.example.fr",
                            email_exp="direction@example.fr",
                        )
                    except ValueError as _smoke_err:
                        assert "Backend de messagerie inconnu" in str(_smoke_err)
                    else:
                        raise AssertionError("backend inconnu accepté")

                    try:
                        _smoke_email.Messagerie(
                            backend="smtp",
                            hote="smtp.example.fr",
                            email_exp="direction@localhost",
                        )
                    except ValueError as _smoke_err:
                        assert "Adresse d'expédition invalide" in str(_smoke_err)
                    else:
                        raise AssertionError("adresse expéditeur invalide acceptée")
                finally:
                    _smoke_email.UTILS_Parametres.Parametres = _smoke_original_parametres
                    _smoke_email.mail.get_connection = _smoke_original_get_connection
                    _smoke_email.smtplib.SMTP = _smoke_original_smtp_class
                    _smoke_mailjet_rest.Client = _smoke_original_mailjet_client

                print("TEAMWORKS_SMOKE_MAILING_STAGE:fixtures", flush=True)
                _smoke_tempdir = _smoke_Path(_smoke_tempfile.mkdtemp(prefix="teamworks-mailing-"))
                _smoke_personal = _smoke_tempdir / "piece-personnelle.txt"
                _smoke_common = _smoke_tempdir / "piece-commune.txt"
                _smoke_personal.write_text("personnelle", encoding="utf-8")
                _smoke_common.write_text("commune", encoding="utf-8")

                _smoke_dialog = _smoke_mailer.Dialog(
                    frame,
                    categorie="saisie_libre",
                    afficher_confirmation_envoi=False,
                )
                _smoke_dialog.Show()
                wx.Yield()

                _smoke_dialog.SetDonnees([
                    {
                        "adresse": "lea@example.technology",
                        "pieces": [str(_smoke_personal)],
                        "champs": {"{PRENOM}": "Léa"},
                    },
                ], modificationAutorisee=True)
                _smoke_dialog.ctrl_objet.SetValue("Rentrée PMSL")

                _smoke_sender = {
                    "moteur": "smtp",
                    "smtp": "smtp.invalid",
                    "port": 587,
                    "utilisateur": "",
                    "motdepasse": "",
                    "adresse": "direction@example.fr",
                    "nom_adresse": "PMSL",
                    "startTLS": True,
                    "parametres": None,
                }
                _smoke_dialog.ctrl_exp.GetDonnees = lambda: dict(_smoke_sender)
                _smoke_dialog.ctrl_pieces.GetDonnees = lambda: [str(_smoke_common)]

                class _SmokeHandler:
                    def __init__(self):
                        self.deleted = 0

                    def DeleteTemporaryImages(self):
                        self.deleted += 1

                _smoke_handlers = []

                def _smoke_get_html(imagesIncluses=True):
                    handler = _SmokeHandler()
                    _smoke_handlers.append(handler)
                    return "<p>Bonjour {PRENOM}</p>", [], handler

                _smoke_dialog.ctrl_editeur.GetValue = lambda: "Bonjour {PRENOM}"
                _smoke_dialog.ctrl_editeur.GetHTML = _smoke_get_html

                _smoke_batches = []

                class _SmokeMessagerie:
                    def __init__(self, **kwargs):
                        self.kwargs = kwargs
                        self.connected = False
                        self.closed = False

                    def Connecter(self):
                        self.connected = True
                        return True

                    def Envoyer_lot(self, messages=None, dlg_progress=None, afficher_confirmation_envoi=True):
                        assert self.connected
                        messages = list(messages or [])
                        _smoke_batches.append(messages)
                        return messages

                    def Fermer(self):
                        self.closed = True

                _smoke_original_messagerie = _smoke_email.Messagerie
                _smoke_email.Messagerie = lambda backend="smtp", **kwargs: _SmokeMessagerie(backend=backend, **kwargs)
                try:
                    print("TEAMWORKS_SMOKE_MAILING_STAGE:first-send", flush=True)
                    _smoke_dialog.OnBoutonEnvoyer(None)
                    wx.Yield()
                    assert len(_smoke_batches) == 1
                    assert len(_smoke_batches[0]) == 1
                    _smoke_first = _smoke_batches[0][0]
                    assert _smoke_first.destinataires == ["lea@example.technology"]
                    assert _smoke_first.sujet == "Rentrée PMSL"
                    assert "Bonjour Léa" in _smoke_first.texte_html
                    assert _smoke_first.fichiers == [str(_smoke_personal), str(_smoke_common)]
                    assert _smoke_dialog.ctrl_destinataires.donnees[0].pieces == [str(_smoke_personal)]

                    print("TEAMWORKS_SMOKE_MAILING_STAGE:second-send", flush=True)
                    _smoke_dialog.OnBoutonEnvoyer(None)
                    wx.Yield()
                    assert len(_smoke_batches) == 2
                    assert len(_smoke_batches[1]) == 1
                    _smoke_second = _smoke_batches[1][0]
                    assert _smoke_second.fichiers == [str(_smoke_personal), str(_smoke_common)]
                    assert _smoke_dialog.ctrl_destinataires.donnees[0].pieces == [str(_smoke_personal)]
                    assert all(handler.deleted == 1 for handler in _smoke_handlers)
                finally:
                    _smoke_email.Messagerie = _smoke_original_messagerie

                _smoke_dialog.Destroy()
                wx.Yield()
                print("TEAMWORKS_SMOKE_MAILING_PREPARATION_READY", flush=True)
            except Exception:
                import traceback as _smoke_traceback
                _smoke_traceback.print_exc()
                print("TEAMWORKS_SMOKE_MAILING_PREPARATION_FAILED", flush=True)
                wx.CallAfter(self.ExitMainLoop)
                return True
            finally:
                try:
                    if _smoke_tempdir is not None:
                        import shutil as _smoke_shutil
                        _smoke_shutil.rmtree(_smoke_tempdir, ignore_errors=True)
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
        raise RuntimeError("injection des marqueurs mailing absente")
    compile(patched_core_source, str(PATCHED_CORE), "exec")
    PATCHED_CORE.write_text(patched_core_source, encoding="utf-8")

    entrypoint_source = ENTRYPOINT_SOURCE.read_text(encoding="utf-8")
    import_line = "import Teamworks_core as CORE"
    patched_import = "import Teamworks_core_mailing_preparation_smoke as CORE"
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
            github_error_summary("Mailing StaticBox parentage failed", output)
            return 4
        if return_code != 0 or FAILURE_MARKER in output:
            github_error_summary("Mailing preparation smoke failed", output)
            return return_code or 1
        if READY_MARKER not in output:
            github_error_summary("Mailing preparation smoke failed", output)
            print("marqueur mailing absent", file=sys.stderr)
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
        github_error_summary("Mailing preparation smoke failed", output)
        return 3
    finally:
        PATCHED.unlink(missing_ok=True)
        PATCHED_CORE.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
