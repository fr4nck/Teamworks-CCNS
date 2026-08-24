from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_heures.py",
    ROOT / "teamworks" / "Dlg" / "DLG_Saisie_presence.py",
)


def _contains_any(source: str, *fragments: str) -> bool:
    return any(fragment in source for fragment in fragments)


def test_time_entries_accept_every_valid_minute() -> None:
    forbidden_fragments = (
        "horaire terminant par 0 ou 5",
        'heureDebut[4] != "5"',
        'heureFin[4] != "5"',
        'heure_debut[4] != "5"',
        'heure_fin[4] != "5"',
    )

    for path in TARGETS:
        source = path.read_text(encoding="utf-8")
        for fragment in forbidden_fragments:
            assert fragment not in source

        assert _contains_any(
            source,
            'heureDebut[3:] >= "60"',
            'heure_debut[3:] >= "60"',
        )
        assert _contains_any(
            source,
            'heureFin[3:] >= "60"',
            'heure_fin[3:] >= "60"',
        )
        assert _contains_any(
            source,
            "if heureDebut > heureFin",
            "if heure_debut > heure_fin",
        )
        compile(source, str(path), "exec")
