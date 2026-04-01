from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.schemas.user import LoginRequest, TokenResponse
from app.services import auth_service

router  = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=TokenResponse, summary="Login with email and password to receive a JWT token")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    """
    Returns a Bearer token valid for 24 hours.
    Use it in all other requests:  Authorization: Bearer <token>
    """
    return await auth_service.login(body)
