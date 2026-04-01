import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)
BASE = "http://test/api/v1"

@pytest.mark.asyncio
async def test_login_admin_success():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": "admin@finance.dev", "password": "Admin@123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert r.json()["user"]["role"] == "admin"

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": "admin@finance.dev", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_login_unknown_email():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": "nobody@test.com", "password": "Whatever@1"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_login_missing_fields():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.post(f"{BASE}/auth/login", json={"email": "admin@finance.dev"})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_protected_route_no_token():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(f"{BASE}/records")
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_protected_route_invalid_token():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(f"{BASE}/records", headers={"Authorization": "Bearer fake.token.here"})
    assert r.status_code == 401
