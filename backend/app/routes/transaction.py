from fastapi import APIRouter, Depends, HTTPException, UploadFile, File  # type: ignore[import]
from sqlalchemy.orm import Session  # type: ignore[import]
from app.database import get_db  # type: ignore[import]
from app.schemas import TransactionCreate, TransactionUpdate, UploadResponse  # type: ignore[import]
from app.services import transaction_service as svc  # type: ignore[import]
from app.utils.csv_parser import parse_csv 

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/", response_model=dict, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    tx = svc.create_transaction(
        db=db,
        description=data.description,
        amount=data.amount,
        category=data.category,
    )
    return tx.to_dict()


@router.get("/", response_model=list[dict])
def get_transactions(db: Session = Depends(get_db)):
    return svc.get_all_with_anomalies(db)


@router.get("/{tx_id}", response_model=dict)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    from app.crud.transaction_crud import get_by_id  # type: ignore[import]
    tx = get_by_id(db, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx.to_dict()


@router.put("/{tx_id}", response_model=dict)
def update_transaction(tx_id: int, data: TransactionUpdate, db: Session = Depends(get_db)):
    tx = svc.update_transaction(db, tx_id, **data.model_dump(exclude_none=True))
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx.to_dict()


@router.delete("/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    success = svc.delete_transaction(db, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Deleted successfully", "id": tx_id}


@router.post("/upload/csv", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()
    rows, parse_errors = parse_csv(contents)

    if not rows:
        raise HTTPException(
            status_code=422,
            detail=f"No valid rows found. Errors: {parse_errors}"
        )

    imported, skipped = svc.bulk_import(db, rows)

    return UploadResponse(
        imported=imported,
        skipped=skipped + len(parse_errors),
        errors=parse_errors[:10],  # type: ignore
    )