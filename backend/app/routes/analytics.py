from fastapi import APIRouter, Depends  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]
from sqlalchemy import func  # type: ignore[import]
from app.database import get_db  # type: ignore[import]
from app.models.transaction import Transaction  # type: ignore[import]

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    txs = db.query(Transaction).all()
    if not txs:
        return {"total": 0, "count": 0, "avg": 0, "max": 0, "anomaly_count": 0}

    amounts = [t.amount for t in txs]
    return {
        "total": round(sum(amounts), 2),
        "count": len(amounts),
        "avg": round(sum(amounts) / len(amounts), 2),  # type: ignore
        "max": round(max(amounts), 2),
        "min": round(min(amounts), 2),
        "anomaly_count": sum(1 for t in txs if t.is_anomaly),
    }


@router.get("/by-category")
def by_category(db: Session = Depends(get_db)):
    results = (
        db.query(Transaction.category, func.sum(Transaction.amount), func.count(Transaction.id))
        .group_by(Transaction.category)
        .all()
    )
    return [
        {"category": r[0], "total": round(r[1], 2), "count": r[2]}
        for r in results
    ]


@router.get("/by-month")
def by_month(db: Session = Depends(get_db)):
    txs = db.query(Transaction).all()
    monthly: dict = {}
    for tx in txs:
        if tx.date:
            key = tx.date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + tx.amount
    return [{"month": k, "total": round(v, 2)} for k, v in sorted(monthly.items())]
