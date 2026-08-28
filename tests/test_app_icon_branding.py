from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "teamworks" / "Icone.ico"
STATIC_ICON = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.ico"
MASTER = ROOT / "teamworks" / "Static" / "Images" / "Branding" / "Teamworks-CCNS.png"
GENERATOR = ROOT / "tools" / "generate_app_icon.py"


def _ico_sizes(path):
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data)
    assert (reserved, kind) == (0, 1)
    sizes = set()
    for index in range(count):
        width, height = struct.unpack_from("<BB", data, 6 + index * 16)
        sizes.add((width or 256, height or 256))
    return sizes


def test_app_icon_is_multiresolution_and_shared_by_runtime_and_packaging():
    expected = {(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                (96, 96), (128, 128), (256, 256)}
    assert expected <= _ico_sizes(ICON)
    assert ICON.read_bytes() == STATIC_ICON.read_bytes()
    assert MASTER.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_icon_generator_uses_the_public_pelemele_palette_and_exact_labels():
    source = GENERATOR.read_text(encoding="utf-8")

    assert 'PELEMELE_ORANGE = "#FFBD59"' in source
    assert 'PELEMELE_SLATE = "#314666"' in source
    assert 'PELEMELE_DEEP_BLUE = "#044576"' in source
    assert '"TW"' in source
    assert '"CCNS"' in source
