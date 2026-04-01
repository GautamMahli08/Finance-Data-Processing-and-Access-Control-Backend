"""
MongoDB database connection using Motor (async driver).
Collections: users, records

Production note:
- All credentials are read from environment variables via config.py
- seed_db() only inserts the admin user if the collection is empty
- Never re-seeds on subsequent startups
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None
db = None

def get_database():
    return db

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    await db.users.create_index("email", unique=True)
    await db.records.create_index("date")
    await db.records.create_index("type")
    await db.records.create_index("category")
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")

async def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

async def seed_db():
    """
    Seeds only the admin user on first startup.
    Admin credentials are read from environment variables.
    All other users must be created manually via POST /api/v1/users.
    """
    from app.core.security import hash_password
    from datetime import datetime, timezone
    import uuid

    def utcnow(): return datetime.now(timezone.utc).isoformat()
    def _id(): return str(uuid.uuid4())

    if await db.users.count_documents({}) > 0:
        print("ℹ️  Database already seeded, skipping.")
        return

    await db.users.insert_one({
        "id": _id(),
        "name": settings.ADMIN_NAME,
        "email": settings.ADMIN_EMAIL,
        "hashed_password": hash_password(settings.ADMIN_PASSWORD),
        "role": "admin",
        "is_active": True,
        "created_at": utcnow(),
    })
    print(f"✅ Admin user seeded: {settings.ADMIN_EMAIL}")
