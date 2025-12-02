# backend/utils/price_parser.py

def normalize_price(price_str: str) -> int:
    # ₹1,299 → 1299
    cleaned = price_str.replace("₹", "").replace(",", "").strip()
    return int(cleaned) if cleaned.isdigit() else None
