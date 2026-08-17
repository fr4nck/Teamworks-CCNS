from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_heures.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
)


def test_time_entries_accept_every_valid_minute() -> None:
    forbidden_fragments = (
        "horaire terminant par 0 ou 5",
        'heureDebut[4] != "5"',
        'heureFin[4] != "5"',
    )

    for path in TARGETS:
        source = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in source

        assert 'heureDebut[3:] >= "60"' in source
        assert 'heureFin[3:] >= "60"' in source
        assert "if heureDebut > heureFin" in source
        compile(source, str(path), "exec")
