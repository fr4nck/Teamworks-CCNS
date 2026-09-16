from pathlib import Path
import warnings

from infrastructure.documents import inspect_twd_bytes

ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    "Autorisation parentale mineurs - Exemple.twd",
    "Certificat de travail - Exemple.twd",
    "Confirmation d'embauche - Exemple.twd",
    "Contrat d'engagement éducatif - Exemple.twd",
    "Contrat à durée déterminée - Exemple.twd",
    "Lettre de refus - Exemple.twd",
)


def test_report_real_twd_inventory_for_iteration_3():
    for generation, base in (
        ("2019", ROOT / "tests" / "fixtures" / "twd" / "real" / "2019"),
        ("2026", ROOT / "teamworks" / "Static" / "Documents"),
    ):
        for filename in MODELS:
            inv = inspect_twd_bytes((base / filename).read_bytes(), source=f"{generation}/{filename}")
            warnings.warn(
                "ITER3_TWD|"
                + "|".join(
                    [
                        generation,
                        filename,
                        inv.source_hash,
                        str(inv.size),
                        inv.xml_declaration,
                        inv.namespace,
                        inv.richtext_version,
                        ",".join(inv.tags),
                        ",".join(inv.attributes),
                        str(inv.paragraph_count),
                        str(inv.text_run_count),
                        str(inv.image_count),
                        ",".join(inv.image_types),
                        str(inv.symbol_count),
                        ",".join(inv.placeholders),
                        ";".join(inv.styles),
                        ",".join(inv.alignments),
                        ",".join(inv.indents),
                        ",".join(inv.colors),
                        ",".join(inv.fonts),
                        ",".join(inv.font_sizes),
                        ",".join(inv.links),
                        str(inv.table_count),
                        str(inv.page_break_count),
                        ",".join(inv.unknown_structures),
                    ]
                ),
                UserWarning,
            )
