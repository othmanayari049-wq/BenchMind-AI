from fastapi.testclient import TestClient

from benchmind.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_endpoint() -> None:
    response = client.post("/api/v1/demo/esp32_wrong_gpio")
    assert response.status_code == 200
    payload = response.json()
    assert payload["diagnosis"]["primary"]["title"] == "ECHO pin-definition mismatch"
    assert payload["verification"]["accepted"] is True
