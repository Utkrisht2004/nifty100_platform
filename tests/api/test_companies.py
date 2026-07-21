from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_companies_list():
    """Verify companies endpoint returns a list structure"""
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_invalid_company():
    """Verify an invalid ticker accurately throws a 404 error"""
    response = client.get("/api/v1/companies/INVALID_TICKER")
    assert response.status_code == 404
