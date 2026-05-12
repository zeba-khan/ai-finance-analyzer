"""
CSV parser for bank statement uploads.
Handles various bank CSV formats (HDFC, ICICI, SBI, generic).
"""
import io
import re
import pandas as pd  # type: ignore[import]
from datetime import datetime


COLUMN_ALIASES = {
    "description": ["description", "narration", "particulars", "remarks", "details", "transaction details"],
    "amount":      ["amount", "debit", "withdrawal", "dr", "debit amount"],
    "date":        ["date", "value date", "transaction date", "txn date"],
}


def _find_column(df: pd.DataFrame, field: str) -> str | None:
    """Find the actual column name for a logical field."""
    aliases = COLUMN_ALIASES[field]
    for col in df.columns:
        if col.strip().lower() in aliases:
            return col
    return None


def _parse_amount(val) -> float | None:
    """Parse amount from string, handling Indian number formatting."""
    if pd.isna(val):
        return None
    s = str(val).replace(",", "").replace("₹", "").replace(" ", "").strip()
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def _parse_date(val) -> datetime | None:
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
        "%d %b %Y", "%d-%b-%Y", "%d/%b/%Y",
        "%m/%d/%Y", "%d.%m.%Y",
    ]
    s = str(val).strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_csv(file_bytes: bytes) -> tuple[list[dict], list[str]]:
    """
    Parse a bank statement CSV.
    Returns (rows, errors) where rows is a list of dicts with keys:
    description, amount, date
    """
    errors = []
    rows = []

    try:
        # Try reading with different encodings
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, skip_blank_lines=True)
                break
            except Exception:
                continue
        else:
            return [], ["Could not decode CSV file. Try UTF-8 or Latin-1 encoding."]

        # Normalize column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.dropna(how="all")

        desc_col = _find_column(df, "description")
        amount_col = _find_column(df, "amount")
        date_col = _find_column(df, "date")

        if not desc_col:
            return [], ["Could not find description/narration column. Columns found: " + ", ".join(df.columns)]
        if not amount_col:
            return [], ["Could not find amount/debit column. Columns found: " + ", ".join(df.columns)]

        for idx, row in df.iterrows():
            desc = str(row[desc_col]).strip()
            if not desc or desc.lower() in ["nan", "none", ""]:
                continue

            amount = _parse_amount(row[amount_col])
            if amount is None:
                errors.append(f"Row {idx+1}: skipped — invalid or zero amount '{row[amount_col]}'")
                continue

            date = None
            if date_col:
                date = _parse_date(row[date_col])
            if date is None:
                date = datetime.utcnow()

            rows.append({
                "description": desc,
                "amount": amount,
                "date": date,
            })

    except Exception as e:
        errors.append(f"Parse error: {str(e)}")

    return rows, errors
