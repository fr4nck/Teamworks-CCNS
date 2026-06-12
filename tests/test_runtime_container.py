from application.bootstrap.bootstrap_runtime import build_runtime_container


def test_runtime_container_is_built():
    container = build_runtime_container()
    assert container is not None
    assert len(container.classifications.list_all()) >= 9
    assert len(container.salary_grids.list_all()) >= 1
    assert len(container.salary_grid_lines.list_all()) >= 1
    assert len(container.calculation_rules.list_all()) >= 5
