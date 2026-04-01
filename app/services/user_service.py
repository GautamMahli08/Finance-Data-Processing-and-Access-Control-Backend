from fastapi import HTTPException
from app.core.database import get_database
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit_service
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc).isoformat()
def _id():    return str(uuid.uuid4())

async def create_user(data: UserCreate, created_by: str) -> dict:
    db = get_database()
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=409, detail=f"Email '{data.email}' is already registered")
    user = {
        "id": _id(), "name": data.name, "email": data.email,
        "hashed_password": hash_password(data.password),
        "role": data.role, "is_active": True,
        "created_at": utcnow(), "updated_at": utcnow(),
    }
    await db.users.insert_one({**user})
    await audit_service.log("create", "user", user["id"], created_by, {"role": data.role, "email": data.email})
    return user

async def list_users() -> list:
    db = get_database()
    return await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(length=1000)

async def get_user(user_id: str) -> dict:
    db = get_database()
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user

async def update_user(user_id: str, data: UserUpdate, updated_by: str) -> dict:
    db = get_database()
    await get_user(user_id)
    updates = data.model_dump(exclude_none=True)
    updates["updated_at"] = utcnow()
    await db.users.update_one({"id": user_id}, {"$set": updates})
    await audit_service.log("update", "user", user_id, updated_by, updates)
    return await get_user(user_id)

async def deactivate_user(user_id: str, requesting_user_id: str) -> dict:
    if user_id == requesting_user_id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    db = get_database()
    await get_user(user_id)
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False, "updated_at": utcnow()}})
    await audit_service.log("delete", "user", user_id, requesting_user_id, {"action": "deactivated"})
    return await get_user(user_id)

async def change_password(user_id: str, old_password: str, new_password: str) -> dict:
    """Allows a user to change their own password after verifying old password"""
    db = get_database()
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(old_password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"hashed_password": hash_password(new_password), "updated_at": utcnow()}}
    )
    await audit_service.log("update", "user", user_id, user_id, {"action": "password_changed"})
    return {"message": "Password changed successfully"}
