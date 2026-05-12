from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.crud import income_crud
from app.models.transaction import Transaction
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/income", tags=["Income"])


class IncomeCreate(BaseModel):
    description: str
    amount: float
    category: Optional[str] = "salary"
    date: Optional[datetime] = None


@router.post("/", status_code=201)
def add_income(data: IncomeCreate, db: Session = Depends(get_db)):
    income = income_crud.create(
        db,
        description=data.description,
        amount=data.amount,
        category=data.category,
        date=data.date,
    )
    return income.to_dict()


@router.get("/")
def get_all_income(db: Session = Depends(get_db)):
    return [i.to_dict() for i in income_crud.get_all(db)]


@router.delete("/{income_id}")
def delete_income(income_id: int, db: Session = Depends(get_db)):
    success = income_crud.delete(db, income_id)
    if not success:
        raise HTTPException(status_code=404, detail="Income not found")
    return {"message": "Deleted", "id": income_id}


@router.get("/summary")
def income_summary(db: Session = Depends(get_db)):
    """Returns income vs expenses vs savings for current month."""
    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")

    # Total income this month
    all_income = income_crud.get_all(db)
    monthly_income = sum(
        i.amount for i in all_income
        if i.date and i.date.strftime("%Y-%m") == month_str
    )
    total_income = sum(i.amount for i in all_income)

    # Total expenses this month
    txs = db.query(Transaction).all()
    monthly_expenses = sum(
        t.amount for t in txs
        if t.date and t.date.strftime("%Y-%m") == month_str
    )
    total_expenses = sum(t.amount for t in txs)

    monthly_savings = monthly_income - monthly_expenses
    total_savings = total_income - total_expenses
    savings_rate = round((monthly_savings / monthly_income * 100), 1) if monthly_income > 0 else 0

    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "monthly_savings": round(monthly_savings, 2),
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "total_savings": round(total_savings, 2),
        "savings_rate": savings_rate,
    }