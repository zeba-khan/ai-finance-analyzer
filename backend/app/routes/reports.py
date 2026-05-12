from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.crud import transaction_crud, income_crud
from app.utils.pdf_generator import generate_monthly_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly/{month_str}")
def get_monthly_report(month_str: str, db: Session = Depends(get_db)):
    """
    Generate and return a PDF report for the given month.
    month_str format: YYYY-MM (e.g. 2024-03)
    """
    transactions = [tx.to_dict() for tx in transaction_crud.get_all(db)]
    income_list  = [i.to_dict()  for i in income_crud.get_all(db)]

    pdf_bytes = generate_monthly_report(
        month_str=month_str,
        transactions=transactions,
        income_list=income_list,
        summary={},
    )

    filename = f"finance_report_{month_str}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )