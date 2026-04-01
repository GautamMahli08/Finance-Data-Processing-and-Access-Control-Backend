from fastapi import APIRouter, Depends
from app.core.deps import require_roles
from app.models.enums import Role
from app.services import record_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def get_summary(
    _ = Depends(require_roles(Role.viewer, Role.analyst, Role.admin))  # All roles
):
    return await record_service.get_summary()

@router.get("/insights")
async def get_insights(
    _ = Depends(require_roles(Role.analyst, Role.admin))  # Analyst + Admin
):
    summary = await record_service.get_summary()
    trends = summary["monthly_trends"]
    insights = []

    if len(trends) >= 2:
        last, prev = trends[-1], trends[-2]
        ic = last["income"]  - prev["income"]
        ec = last["expense"] - prev["expense"]
        insights += [
            {"metric": "Income MoM Change",  "value": ic, "direction": "up" if ic >= 0 else "down"},
            {"metric": "Expense MoM Change", "value": ec, "direction": "up" if ec >= 0 else "down"},
        ]

    top = max(
        [c for c in summary["category_totals"] if c["type"] == "expense"],
        key=lambda x: x["total"], default=None
    )
    if top:
        insights.append({"metric": "Top Expense Category", "value": top["category"], "total": top["total"]})

    return {"insights": insights, "summary": summary}
