from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_execution():
    """Verify screener endpoints run effectively under param bounds"""
    response = client.get("/api/v1/screener/?min_roe=15&max_de=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
