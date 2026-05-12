from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.sms_parser import parse_sms
from app.services import transaction_service as svc
from app.crud import income_crud
from pydantic import BaseModel

router = APIRouter(prefix="/sms", tags=["SMS Parser"])


class SMSInput(BaseModel):
    sms_text: str


@router.post("/parse")
def parse_and_preview(data: SMSInput):
    """Just parse — don't save. For preview before confirming."""
    result = parse_sms(data.sms_text)
    if not result:
        return {"success": False, "error": "Could not extract transaction from SMS"}
    return {"success": True, "parsed": result}


@router.post("/import")
def parse_and_import(data: SMSInput, db: Session = Depends(get_db)):
    """Parse SMS and directly save as transaction or income."""
    result = parse_sms(data.sms_text)
    if not result:
        return {"success": False, "error": "Could not extract transaction from SMS"}

    if result["type"] == "debit":
        tx = svc.create_transaction(
            db=db,
            description=result["description"],
            amount=result["amount"],
            source="sms",
        )
        return {
            "success": True,
            "type": "expense",
            "saved": tx.to_dict(),
        }
    else:
        income = income_crud.create(
            db=db,
            description=result["description"],
            amount=result["amount"],
            category="other",
            date=result["date"],
        )
        return {
            "success": True,
            "type": "income",
            "saved": income.to_dict(),
        }


@router.post("/bulk-import")
def bulk_sms_import(data: dict, db: Session = Depends(get_db)):
    """Import multiple SMS messages at once."""
    sms_list = data.get("sms_list", [])
    imported = 0
    skipped = 0
    results = []

    for sms in sms_list:
        result = parse_sms(sms)
        if not result:
            skipped += 1
            continue

        if result["type"] == "debit":
            tx = svc.create_transaction(
                db=db,
                description=result["description"],
                amount=result["amount"],
                source="sms",
            )
            results.append({"type": "expense", "saved": tx.to_dict()})
        else:
            income = income_crud.create(
                db=db,
                description=result["description"],
                amount=result["amount"],
                category="other",
                date=result["date"],
            )
            results.append({"type": "income", "saved": income.to_dict()})
        imported += 1

    return {
        "imported": imported,
        "skipped": skipped,
        "results": results,
    }