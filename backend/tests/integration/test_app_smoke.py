from app.main import app


def test_app_exposes_expected_routes() -> None:
    paths = set(app.openapi()["paths"].keys())

    assert "/health" in paths
    assert "/" in paths
    assert "/api/v1/analyze" in paths
    assert "/api/v1/analyze/file" in paths
    assert "/api/v1/redact" in paths
    assert "/api/v1/redact/file" in paths
