from application.bootstrap.bootstrap_runtime import build_runtime_container


def test_runtime_bootstrap_smoke():
    runtime = build_runtime_container()
    assert runtime.classifications.get_by_code("G3") is not None
    assert runtime.salary_grids.get_by_code("CCNS-2026") is not None
