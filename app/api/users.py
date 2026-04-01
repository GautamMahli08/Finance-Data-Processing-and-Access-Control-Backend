from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, require_roles
from app.models.enums import Role
from app.schemas.user import UserCreate, UserUpdate, UserOut, ChangePasswordRequest
from app.services import user_service, audit_service
from typing import Optional
from fastapi import Query

router = APIRouter(prefix="/users", tags=["Users"])

admin_dep = Depends(require_roles(Role.admin))

@router.get("/me", response_model=UserOut, summary="Get your own profile")
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)

@router.get("", summary="List all users (Admin only)")
async def list_users(_ = admin_dep):
    users = await user_service.list_users()
    return [UserOut(**u) for u in users]

@router.post("", response_model=UserOut, status_code=201, summary="Create a new user (Admin only)")
async def create_user(body: UserCreate, current_user: dict = Depends(require_roles(Role.admin))):
    return UserOut(**await user_service.create_user(body, current_user["id"]))

@router.get("/{user_id}", response_model=UserOut, summary="Get user by ID (Admin only)")
async def get_user(user_id: str, _ = admin_dep):
    return UserOut(**await user_service.get_user(user_id))

@router.patch("/{user_id}", response_model=UserOut, summary="Update user name/role/status (Admin only)")
async def update_user(user_id: str, body: UserUpdate, current_user: dict = Depends(require_roles(Role.admin))):
    return UserOut(**await user_service.update_user(user_id, body, current_user["id"]))

@router.delete("/{user_id}", response_model=UserOut, summary="Deactivate a user (Admin only)")
async def deactivate_user(user_id: str, current_user: dict = Depends(require_roles(Role.admin))):
    return UserOut(**await user_service.deactivate_user(user_id, current_user["id"]))

@router.post("/me/change-password", summary="Change your own password")
async def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    return await user_service.change_password(current_user["id"], body.old_password, body.new_password)
