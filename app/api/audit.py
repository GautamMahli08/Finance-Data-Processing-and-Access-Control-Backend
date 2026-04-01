"""
Audit Log API
- Admin: can see all audit logs
- Analyst: can see their own actions only
- Viewer: no access
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.deps import get_current_user, require_roles
from app.models.enums import Role
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("", summary="View audit logs — Admin sees all, Analyst sees own actions")
async def get_audit_logs(
    resource:  Optional[str] = Query(None, description="Filter by resource: record | user"),
    page:      int            = Query(1,   ge=1),
    page_size: int            = Query(50,  ge=1, le=100),
    current_user: dict = Depends(require_roles(Role.analyst, Role.admin)),
):
    # Analyst can only see their own actions
    performed_by = None if current_user["role"] == "admin" else current_user["id"]
    items, total = await audit_service.get_logs(resource=resource, performed_by=performed_by, page=page, page_size=page_size)
    return {
        "items":     items,
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     (total + page_size - 1) // page_size,
    }
