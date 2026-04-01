from fastapi import HTTPException, status
from app.core.database import get_database
from app.core.security import verify_password, create_access_token
from app.schemas.user import LoginRequest
from app.services import audit_service

async def login(data: LoginRequest) -> dict:
    db = get_database()
    user = await db.users.find_one({"email": data.email}, {"_id": 0})

    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact an admin.",
        )

    token = create_access_token({"sub": user["id"], "role": user["role"]})
    await audit_service.log("login", "user", user["id"], user["id"], {"email": user["email"]})

    safe_user = {k: v for k, v in user.items() if k != "hashed_password"}
    return {"access_token": token, "token_type": "bearer", "user": safe_user}

async def get_user_from_token(token: str) -> dict:
    from app.core.security import decode_access_token
    from fastapi import HTTPException, status
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    db = get_database()
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    return user
