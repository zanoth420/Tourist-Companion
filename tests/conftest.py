import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """API client backed by a throwaway database."""
    monkeypatch.setenv("TC_DB_PATH", str(tmp_path / "test.db"))
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def user(client):
    """A registered, logged-in user (session cookie set on the client)."""
    res = client.post("/api/auth/register", json={
        "name": "Test User", "email": "test@example.com", "password": "secret123"})
    assert res.status_code == 201
    return res.json()
