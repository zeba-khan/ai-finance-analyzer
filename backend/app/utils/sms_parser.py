"""
Bank SMS parser for Indian banks.
Supports HDFC, ICICI, SBI, Axis, Kotak, and generic formats.
"""
import re
from datetime import datetime


# ── Amount patterns ────────────────────────────────────────
AMOUNT_PATTERNS = [
    r"INR\s*([\d,]+\.?\d*)",           # INR 320.00
    r"Rs\.?\s*([\d,]+\.?\d*)",         # Rs. 320 or Rs 320
    r"₹\s*([\d,]+\.?\d*)",            # ₹320
    r"debited.*?(\d[\d,]+\.?\d*)",     # debited 320.00
    r"credited.*?(\d[\d,]+\.?\d*)",    # credited 50000
    r"withdrawn.*?(\d[\d,]+\.?\d*)",   # withdrawn 500
]

# ── Date patterns ──────────────────────────────────────────
DATE_PATTERNS = [
    (r"\b(\d{2}-\d{2}-\d{2})\b",   "%d-%m-%y"),   # 01-03-24
    (r"\b(\d{2}/\d{2}/\d{4})\b",   "%d/%m/%Y"),   # 01/03/2024
    (r"\b(\d{2}-\d{2}-\d{4})\b",   "%d-%m-%Y"),   # 01-03-2024
    (r"\b(\d{4}-\d{2}-\d{2})\b",   "%Y-%m-%d"),   # 2024-03-01
    (r"\b(\d{2}\s\w{3}\s\d{4})\b", "%d %b %Y"),   # 01 Mar 2024
]

# ── Merchant extraction keywords ───────────────────────────
DEBIT_KEYWORDS  = ["debited", "debit", "withdrawn", "paid", "purchase", "spent"]
CREDIT_KEYWORDS = ["credited", "credit", "received", "deposited", "salary"]

# ── Known merchant patterns ────────────────────────────────
MERCHANT_PATTERNS = [
    r"(?:at|to|for|towards|via)\s+([A-Za-z0-9\s]+?)(?:\s+on|\s+ref|\s+upi|\.|$)",
    r"trf\s+(?:to|from)\s+([A-Za-z0-9\s]+?)(?:\s+ref|\s+upi|\.|$)",
    r"UPI[-/]([A-Za-z0-9\s]+?)(?:@|\s+ref|\.|$)",
]


def _extract_amount(sms: str) -> float | None:
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, sms, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                return float(amount_str)
            except ValueError:
                continue
    return None


def _extract_date(sms: str) -> datetime | None:
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, sms)
        if match:
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue
    return datetime.utcnow()


def _extract_merchant(sms: str) -> str:
    for pattern in MERCHANT_PATTERNS:
        match = re.search(pattern, sms, re.IGNORECASE)
        if match:
            merchant = match.group(1).strip()
            if len(merchant) > 2:
                return merchant.title()

    # Fallback: look for known brand names
    known_brands = [
        "Swiggy", "Zomato", "Uber", "Ola", "Amazon", "Flipkart",
        "Netflix", "Spotify", "IRCTC", "PhonePe", "Paytm", "BigBasket",
        "Blinkit", "Dunzo", "Myntra", "Nykaa", "Meesho",
    ]
    for brand in known_brands:
        if brand.lower() in sms.lower():
            return brand

    return "Bank Transaction"


def _is_debit(sms: str) -> bool:
    sms_lower = sms.lower()
    for kw in CREDIT_KEYWORDS:
        if kw in sms_lower:
            return False
    return True


def parse_sms(sms_text: str) -> dict | None:
    """
    Parse a bank SMS and return transaction dict.
    Returns None if parsing fails.
    """
    sms_text = sms_text.strip()
    if not sms_text:
        return None

    amount = _extract_amount(sms_text)
    if not amount:
        return None

    # Skip credit SMS (salary/refund) — treat as income not expense
    if not _is_debit(sms_text):
        return {
            "type": "credit",
            "description": _extract_merchant(sms_text),
            "amount": amount,
            "date": _extract_date(sms_text),
        }

    return {
        "type": "debit",
        "description": _extract_merchant(sms_text),
        "amount": amount,
        "date": _extract_date(sms_text),
    }