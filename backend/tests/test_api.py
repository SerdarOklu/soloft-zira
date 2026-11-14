from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta_reports_unfinished_parameters():
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["default_climate_profile"] == "semi_arid_continental"
    assert "winter_wheat" in body["crops"]
    assert "field_memory.ndvi_cropped_threshold" in body["parameters_unset"]
    assert "core.sufficiency_ratio" in body["parameters_needing_signoff"]
