from tools.migrate_six_py2_decode_branches import migrate_source


def test_removes_isolated_decode_branch():
    source = (
        "value = get_value()\n"
        "if six.PY2:\n"
        "    value = value.decode('iso-8859-15')\n"
        "consume(value)\n"
    )

    migrated, count = migrate_source(source)

    assert count == 1
    assert migrated == "value = get_value()\nconsume(value)\n"


def test_preserves_branch_with_multiple_statements():
    source = (
        "if six.PY2:\n"
        "    first = first.decode('iso-8859-15')\n"
        "    second = second.decode('iso-8859-15')\n"
        "consume(first, second)\n"
    )

    migrated, count = migrate_source(source)

    assert count == 0
    assert migrated == source


def test_preserves_non_decode_branch():
    source = (
        "if six.PY2:\n"
        "    value = transform(value)\n"
        "consume(value)\n"
    )

    migrated, count = migrate_source(source)

    assert count == 0
    assert migrated == source
