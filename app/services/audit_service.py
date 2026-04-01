"""
Audit Log Service
Tracks every write action (create, update, delete) by whom and when.
Analysts and Admins can view logs. Only Admin sees all logs.
"""
from app.core.database import get_database
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc).isoformat()

async def log(action: str, resource: str, resource_id: str, performed_by: str, detail: dict = None):
    """
    action      : "create" | "update" | "delete" | "login"
    resource    : "record" | "user"
    resource_id : id of the affected document
    performed_by: user id of who did the action
    """
    db = get_database()
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "performed_by": performed_by,
        "detail": detail or {},
        "timestamp": utcnow(),
    })

async def get_logs(resource: str = None, performed_by: str = None, page: int = 1, page_size: int = 50):
    db = get_database()
    query = {}
    if resource:     query["resource"]     = resource
    if performed_by: query["performed_by"] = performed_by
    total  = await db.audit_logs.count_documents(query)
    offset = (page - 1) * page_size
    items  = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(page_size).to_list(length=page_size)
    return items, total
