import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)
BASE = "http://test/api/v1"

async def get_token(client, email, password):
    r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_admin_can_create_user():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.post(f"{BASE}/users",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Analyst", "email": "testanalyst@x.com", "password": "Test@1234", "role": "analyst"})
    assert r.status_code == 201
    assert r.json()["role"] == "analyst"

@pytest.mark.asyncio
async def test_duplicate_email_rejected():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        headers = {"Authorization": f"Bearer {token}"}
        await c.post(f"{BASE}/users", headers=headers,
            json={"name": "A", "email": "dup@x.com", "password": "Dup@12345", "role": "viewer"})
        r = await c.post(f"{BASE}/users", headers=headers,
            json={"name": "B", "email": "dup@x.com", "password": "Dup@12345", "role": "viewer"})
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_weak_password_rejected():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.post(f"{BASE}/users",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Weak", "email": "weak@x.com", "password": "weak", "role": "viewer"})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_get_my_profile():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.get(f"{BASE}/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "admin@finance.dev"

@pytest.mark.asyncio
async def test_non_admin_cannot_list_users():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        admin_token = await get_token(c, "admin@finance.dev", "Admin@123")
        await c.post(f"{BASE}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Viewer", "email": "viewer2@x.com", "password": "View@1234", "role": "viewer"})
        viewer_token = await get_token(c, "viewer2@x.com", "View@1234")
        r = await c.get(f"{BASE}/users", headers={"Authorization": f"Bearer {viewer_token}"})
    assert r.status_code == 403
