from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.models.enums import RecordType

class RecordCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Must be greater than 0")
    type: RecordType
    category: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., description="Format: YYYY-MM-DD")
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

class RecordUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

class RecordOut(BaseModel):
    id: str
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str] = None
    created_by: str
    is_deleted: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class RecordFilter(BaseModel):
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None        # ← NEW: search in notes + category
    page: int = 1
    page_size: int = 20
