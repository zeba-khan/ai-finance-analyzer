"""
All database query logic lives here.
Routes call services, services call crud — never routes calling DB directly.
"""
from sqlalchemy.orm import Session  # type: ignore[import]
from sqlalchemy import desc
from datetime import datetime
from app.models.transaction import Transaction  # type: ignore[import]


def create(db: Session, description: str, amount: float, category: str,
           confidence: float, date: datetime = None, source: str = "manual") -> Transaction:  # type: ignore[import]
    tx = Transaction(
        description=description,
        amount=amount,
        category=category,
        confidence=confidence,
        date=date or datetime.utcnow(),
        source=source,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_all(db: Session) -> list[Transaction]:
    return db.query(Transaction).order_by(desc(Transaction.date)).all()


def get_by_id(db: Session, tx_id: int) -> Transaction | None:
    return db.query(Transaction).filter(Transaction.id == tx_id).first()

def duplicate_exists(
    db: Session,
    description: str,
    amount: float,
    date: datetime,
) -> bool:
    return db.query(Transaction).filter(
        Transaction.description == description,
        Transaction.amount == amount,
        Transaction.date == date,
    ).first() is not None   


def update(db: Session, tx: Transaction, **fields) -> Transaction:
    for key, val in fields.items():
        if val is not None:
            setattr(tx, key, val)
    db.commit()
    db.refresh(tx)
    return tx


def delete(db: Session, tx: Transaction) -> None:
    db.delete(tx)
    db.commit()


def bulk_create(db: Session, items: list[dict]) -> list[Transaction]:
    txs = [Transaction(**item) for item in items]
    db.bulk_save_objects(txs, return_defaults=True)
    db.commit()
    # Refresh to get IDs
    for tx in txs:
        db.refresh(tx)
    return txs


def update_anomaly_scores(db: Session, ids: list[int],
                          flags: list[int], scores: list[float]) -> None:
    for tx_id, flag, score in zip(ids, flags, scores):
        db.query(Transaction).filter(Transaction.id == tx_id).update(
            {"is_anomaly": bool(flag), "anomaly_score": score},
            synchronize_session=False,
        )
    db.commit()
