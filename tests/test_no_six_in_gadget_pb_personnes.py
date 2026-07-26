from pathlib import Path


SOURCE_PATH = Path("teamworks/Ctrl/CTRL_Gadget_pb_personnes.py")


def test_no_six_dependency_remains_in_gadget_pb_personnes():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "import six" not in source
    assert "six." not in source


def test_gadget_pb_personnes_uses_native_python3_text_type():
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert "isinstance(item, str)" in source
