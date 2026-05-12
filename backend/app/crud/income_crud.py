from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.models.income import Income


def create(db: Session, description: str, amount: float,
           category: str = "salary", date: datetime = None) -> Income:
    income = Income(
        description=description,
        amount=amount,
        category=category,
        date=date or datetime.utcnow(),
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def get_all(db: Session) -> list[Income]:
    return db.query(Income).order_by(desc(Income.date)).all()


def delete(db: Session, income_id: int) -> bool:
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        return False
    db.delete(income)
    db.commit()
    return True