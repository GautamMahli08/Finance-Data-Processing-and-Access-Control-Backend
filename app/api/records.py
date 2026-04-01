from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.core.deps import require_roles
from app.models.enums import Role, RecordType
from app.schemas.record import RecordCreate, RecordUpdate, RecordOut, RecordFilter
from app.services import record_service

router = APIRouter(prefix="/records", tags=["Financial Records"])

read_dep  = Depends(require_roles(Role.viewer, Role.analyst, Role.admin))
admin_dep = Depends(require_roles(Role.admin))

@router.get("", summary="List records — filter by type, category, date, search. Supports pagination.")
async def list_records(
    type:      Optional[RecordType] = Query(None, description="income | expense"),
    category:  Optional[str]        = Query(None, description="Exact category name (case-insensitive)"),
    date_from: Optional[str]        = Query(None, description="Start date YYYY-MM-DD"),
    date_to:   Optional[str]        = Query(None, description="End date YYYY-MM-DD"),
    search:    Optional[str]        = Query(None, description="Partial match in category or notes"),
    page:      int                  = Query(1,    ge=1),
    page_size: int                  = Query(20,   ge=1, le=100),
    _ = read_dep,
):
    items, total = await record_service.list_records(
        RecordFilter(type=type, category=category, date_from=date_from,
                     date_to=date_to, search=search, page=page, page_size=page_size)
    )
    return {
        "items":     [RecordOut(**r) for r in items],
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     (total + page_size - 1) // page_size,
    }

@router.post("", response_model=RecordOut, status_code=201, summary="Create record (Admin only)")
async def create_record(body: RecordCreate, current_user: dict = Depends(require_roles(Role.admin))):
    return RecordOut(**await record_service.create_record(body, current_user["id"]))

@router.get("/{record_id}", response_model=RecordOut, summary="Get single record by ID")
async def get_record(record_id: str, _ = read_dep):
    return RecordOut(**await record_service.get_record(record_id))

@router.patch("/{record_id}", response_model=RecordOut, summary="Update record (Admin only)")
async def update_record(record_id: str, body: RecordUpdate, current_user: dict = Depends(require_roles(Role.admin))):
    return RecordOut(**await record_service.update_record(record_id, body, current_user["id"]))

@router.delete("/{record_id}", status_code=204, summary="Soft delete record (Admin only)")
async def delete_record(record_id: str, current_user: dict = Depends(require_roles(Role.admin))):
    await record_service.delete_record(record_id, current_user["id"])
