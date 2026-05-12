from sqlalchemy.orm import Session
from app.models.budget import Budget

def get_all(db: Session) -> list[Budget]:
    return db.query(Budget).all()

def get_by_category(db: Session, category: str) -> Budget | None:
    return db.query(Budget).filter(Budget.category == category).first()

def upsert(db: Session, category: str, amount: float) -> Budget:
    """Update if exists, create if not."""
    budget = get_by_category(db, category)
    if budget:
        budget.amount = amount
    else:
        budget = Budget(category=category, amount=amount)
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget

def delete(db: Session, category: str) -> bool:
    budget = get_by_category(db, category)
    if not budget:
        return False
    db.delete(budget)
    db.commit()
    return True