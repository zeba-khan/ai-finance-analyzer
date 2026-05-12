from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.transaction import Transaction
from app.crud import budget_crud
from pydantic import BaseModel

router = APIRouter(prefix="/budgets", tags=["Budgets"])

class BudgetSet(BaseModel):
    category: str
    amount: float

@router.get("/")
def get_budgets(db: Session = Depends(get_db)):
    return [b.to_dict() for b in budget_crud.get_all(db)]

@router.post("/")
def set_budget(data: BudgetSet, db: Session = Depends(get_db)):
    budget = budget_crud.upsert(db, data.category, data.amount)
    return budget.to_dict()

@router.delete("/{category}")
def delete_budget(category: str, db: Session = Depends(get_db)):
    success = budget_crud.delete(db, category)
    return {"deleted": success}

@router.get("/status")
def budget_status(db: Session = Depends(get_db)):
    """Returns how much spent vs budget for each category this month."""
    from datetime import datetime
    budgets = budget_crud.get_all(db)
    if not budgets:
        return []

    # Get current month spending per category
    now = datetime.utcnow()
    results = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(
            func.strftime("%Y-%m", Transaction.date) == now.strftime("%Y-%m")
        )
        .group_by(Transaction.category)
        .all()
    )
    spent_map = {r[0]: r[1] for r in results}

    status = []
    for b in budgets:
        spent = spent_map.get(b.category, 0)
        percent = round((spent / b.amount) * 100, 1) if b.amount > 0 else 0
        status.append({
            "category": b.category,
            "budget": b.amount,
            "spent": round(spent, 2),
            "remaining": round(b.amount - spent, 2),
            "percent": percent,
            "status": (
                "exceeded" if percent > 100
                else "warning" if percent > 90
                else "ok"
            )
        })
    return status