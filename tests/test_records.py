import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

transport = ASGITransport(app=app)
BASE = "http://test/api/v1"

async def get_token(client, email, password):
    r = await client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]

INCOME = {"amount": 75000, "type": "income", "category": "Salary", "date": "2025-04-15", "notes": "April salary"}
EXPENSE = {"amount": 18000, "type": "expense", "category": "Rent",   "date": "2025-04-05", "notes": "April rent"}

@pytest.mark.asyncio
async def test_admin_can_create_record():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.post(f"{BASE}/records", headers={"Authorization": f"Bearer {token}"}, json=INCOME)
    assert r.status_code == 201
    assert r.json()["amount"] == 75000

@pytest.mark.asyncio
async def test_negative_amount_rejected():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.post(f"{BASE}/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": -500, "type": "expense", "category": "Misc", "date": "2025-04-01"})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_invalid_date_rejected():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        r = await c.post(f"{BASE}/records",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": 500, "type": "expense", "category": "Misc", "date": "01-04-2025"})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_viewer_cannot_create_record():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        admin_token = await get_token(c, "admin@finance.dev", "Admin@123")
        await c.post(f"{BASE}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "V", "email": "v@x.com", "password": "View@1234", "role": "viewer"})
        viewer_token = await get_token(c, "v@x.com", "View@1234")
        r = await c.post(f"{BASE}/records", headers={"Authorization": f"Bearer {viewer_token}"}, json=INCOME)
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_analyst_cannot_create_record():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        admin_token = await get_token(c, "admin@finance.dev", "Admin@123")
        await c.post(f"{BASE}/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "An", "email": "an@x.com", "password": "Anal@1234", "role": "analyst"})
        analyst_token = await get_token(c, "an@x.com", "Anal@1234")
        r = await c.post(f"{BASE}/records", headers={"Authorization": f"Bearer {analyst_token}"}, json=INCOME)
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_list_records_with_filter():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        headers = {"Authorization": f"Bearer {token}"}
        await c.post(f"{BASE}/records", headers=headers, json=INCOME)
        await c.post(f"{BASE}/records", headers=headers, json=EXPENSE)
        r = await c.get(f"{BASE}/records?type=income", headers=headers)
    assert r.status_code == 200
    assert all(item["type"] == "income" for item in r.json()["items"])

@pytest.mark.asyncio
async def test_search_records():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        headers = {"Authorization": f"Bearer {token}"}
        await c.post(f"{BASE}/records", headers=headers, json=INCOME)
        r = await c.get(f"{BASE}/records?search=salary", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1

@pytest.mark.asyncio
async def test_soft_delete_record():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        headers = {"Authorization": f"Bearer {token}"}
        created = await c.post(f"{BASE}/records", headers=headers, json=INCOME)
        rid = created.json()["id"]
        del_r = await c.delete(f"{BASE}/records/{rid}", headers=headers)
        assert del_r.status_code == 204
        get_r = await c.get(f"{BASE}/records/{rid}", headers=headers)
        assert get_r.status_code == 404

@pytest.mark.asyncio
async def test_dashboard_summary():
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await get_token(c, "admin@finance.dev", "Admin@123")
        headers = {"Authorization": f"Bearer {token}"}
        await c.post(f"{BASE}/records", headers=headers, json=INCOME)
        await c.post(f"{BASE}/records", headers=headers, json=EXPENSE)
        r = await c.get(f"{BASE}/dashboard/summary", headers=headers)
    assert r.status_code == 200
    j = r.json()
    assert "total_income" in j and "total_expense" in j and "net_balance" in j
