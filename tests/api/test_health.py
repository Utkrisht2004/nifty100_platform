from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_health_endpoint():
    """Verify health endpoint returns a successful 200 check with ok status"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
