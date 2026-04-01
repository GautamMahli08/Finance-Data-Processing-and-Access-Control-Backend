from fastapi import HTTPException
from app.core.database import get_database
from app.schemas.record import RecordCreate, RecordUpdate, RecordFilter
from app.services import audit_service
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc).isoformat()
def _id():    return str(uuid.uuid4())

async def create_record(data: RecordCreate, user_id: str) -> dict:
    db = get_database()
    record = {
        "id": _id(), "amount": data.amount, "type": data.type,
        "category": data.category, "date": data.date, "notes": data.notes,
        "created_by": user_id, "is_deleted": False,
        "created_at": utcnow(), "updated_at": utcnow(),
    }
    await db.records.insert_one({**record})
    await audit_service.log("create", "record", record["id"], user_id, {"type": data.type, "amount": data.amount})
    return record

async def list_records(f: RecordFilter):
    db = get_database()
    query = {"is_deleted": False}
    if f.type:      query["type"]     = f.type
    if f.category:  query["category"] = {"$regex": f"^{f.category}$", "$options": "i"}
    if f.date_from: query.setdefault("date", {})["$gte"] = f.date_from
    if f.date_to:   query.setdefault("date", {})["$lte"] = f.date_to
    if f.search:
        query["$or"] = [
            {"notes":    {"$regex": f.search, "$options": "i"}},
            {"category": {"$regex": f.search, "$options": "i"}},
        ]
    total  = await db.records.count_documents(query)
    offset = (f.page - 1) * f.page_size
    items  = await db.records.find(query, {"_id": 0}).sort("date", -1).skip(offset).limit(f.page_size).to_list(length=f.page_size)
    return items, total

async def get_record(record_id: str) -> dict:
    db = get_database()
    record = await db.records.find_one({"id": record_id, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found or has been deleted")
    return record

async def update_record(record_id: str, data: RecordUpdate, user_id: str) -> dict:
    db = get_database()
    await get_record(record_id)
    updates = data.model_dump(exclude_none=True)
    updates["updated_at"] = utcnow()
    await db.records.update_one({"id": record_id}, {"$set": updates})
    await audit_service.log("update", "record", record_id, user_id, updates)
    return await get_record(record_id)

async def delete_record(record_id: str, user_id: str):
    """Soft delete — sets is_deleted=True, record remains in DB for audit trail"""
    db = get_database()
    await get_record(record_id)
    await db.records.update_one({"id": record_id}, {"$set": {"is_deleted": True, "updated_at": utcnow()}})
    await audit_service.log("delete", "record", record_id, user_id)

async def get_summary() -> dict:
    db = get_database()
    kpi_result = await db.records.aggregate([
        {"$match": {"is_deleted": False}},
        {"$group": {"_id": "$type", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}}
    ]).to_list(length=10)

    total_income = total_expense = record_count = 0
    for k in kpi_result:
        record_count += k["count"]
        if k["_id"] == "income":  total_income  = round(k["total"], 2)
        if k["_id"] == "expense": total_expense = round(k["total"], 2)

    cat_result = await db.records.aggregate([
        {"$match": {"is_deleted": False}},
        {"$group": {"_id": {"type": "$type", "category": "$category"}, "total": {"$sum": "$amount"}}},
        {"$sort": {"_id.type": 1, "_id.category": 1}}
    ]).to_list(length=1000)
    category_totals = [{"type": c["_id"]["type"], "category": c["_id"]["category"], "total": round(c["total"], 2)} for c in cat_result]

    monthly_raw = await db.records.aggregate([
        {"$match": {"is_deleted": False}},
        {"$addFields": {"month": {"$substr": ["$date", 0, 7]}}},
        {"$group": {"_id": {"month": "$month", "type": "$type"}, "total": {"$sum": "$amount"}}},
        {"$sort": {"_id.month": 1}}
    ]).to_list(length=1000)
    monthly_map = {}
    for m in monthly_raw:
        mo = m["_id"]["month"]
        if mo not in monthly_map: monthly_map[mo] = {"income": 0, "expense": 0}
        monthly_map[mo][m["_id"]["type"]] = round(m["total"], 2)
    monthly_trends = [{"month": mo, **monthly_map[mo]} for mo in sorted(monthly_map)]

    recent = await db.records.find({"is_deleted": False}, {"_id": 0}).sort("date", -1).limit(10).to_list(length=10)

    return {
        "total_income":    total_income,
        "total_expense":   total_expense,
        "net_balance":     round(total_income - total_expense, 2),
        "record_count":    record_count,
        "category_totals": category_totals,
        "monthly_trends":  monthly_trends,
        "recent_activity": recent,
    }
