"""
Business logic layer. Orchestrates ML, CRUD, and RAG.
"""
from sqlalchemy.orm import Session  # type: ignore[import]
from app.crud import transaction_crud as crud  # type: ignore[import]
from app.ml.classifier import predict_category  # type: ignore[import]
from app.ml.anomaly import detect, train_and_save, invalidate_model  # type: ignore[import]
from app.ml.rag_engine import upsert_transaction, upsert_many, delete_transaction as rag_delete_transaction
from app.models.transaction import Transaction  # type: ignore[import]


def create_transaction(db: Session, description: str, amount: float,
                       category: str = None, source: str = "manual") -> Transaction:  # type: ignore
    # Predict category if not provided
    if not category:
        category, confidence = predict_category(description)
    else:
        _, confidence = predict_category(description)

    tx = crud.create(
        db=db,
        description=description,
        amount=amount,
        category=category,
        confidence=confidence,
        source=source,
    )

    # Sync to vector DB for RAG
    upsert_transaction(tx.to_dict())

    # Invalidate anomaly model so it retrains with new data
    invalidate_model()

    return tx


def get_all_with_anomalies(db: Session) -> list[dict]:
    transactions = crud.get_all(db)
    if not transactions:
        return []

    data = [tx.to_dict() for tx in transactions]

    # Run anomaly detection
    flags, scores = detect(data)

    # Persist updated anomaly scores
    ids = [tx["id"] for tx in data]
    crud.update_anomaly_scores(db, ids, flags, scores)

    for i, tx in enumerate(data):
        tx["is_anomaly"] = bool(flags[i])
        tx["anomaly_score"] = round(scores[i], 4)

    return data


def update_transaction(db: Session, tx_id: int, **fields) -> Transaction | None:
    tx = crud.get_by_id(db, tx_id)
    if not tx:
        return None

    # Re-predict if description changed
    if "description" in fields and fields["description"]:
        new_category, new_conf = predict_category(fields["description"])
        if "category" not in fields or not fields["category"]:
            fields["category"] = new_category
        fields["confidence"] = new_conf

    tx = crud.update(db, tx, **fields)
    upsert_transaction(tx.to_dict())
    invalidate_model()
    return tx


def delete_transaction(db: Session, tx_id: int) -> bool:
    tx = crud.get_by_id(db, tx_id)
    if not tx:
        return False
    crud.delete(db, tx)
    rag_delete_transaction(tx_id)  # remove from vector DB
    invalidate_model()
    return True


def bulk_import(db: Session, rows: list[dict]) -> tuple[int, int]:
    """Import parsed CSV rows. Returns (imported_count, skipped_count)."""
    imported = 0
    skipped = 0
    created_txs = []

    for row in rows:
        try:
            if crud.duplicate_exists(
                db=db,
                description=row["description"],
                amount=row["amount"],
                date=row.get("date"),
            ):
                skipped += 1
                continue
            cat, conf = predict_category(row["description"])
            tx = crud.create(
                db=db,
                description=row["description"],
                amount=row["amount"],
                category=cat,
                confidence=conf,
                date=row.get("date"),
                source="csv_upload",
            )
            created_txs.append(tx.to_dict())
            imported += 1  # type: ignore
        except Exception:
            skipped += 1  # type: ignore

    # Bulk sync to vector DB
    if created_txs:
        upsert_many(created_txs)
        invalidate_model()

    return imported, skipped
