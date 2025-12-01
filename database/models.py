# database/models.py
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class ScrapedProduct:
    name: str
    price: Optional[float]
    url: Optional[str]
    source: str = ""
    image_url: Optional[str] = None
    original_price: Optional[float] = None
    product_id: Optional[str] = None

    @staticmethod
    def clean_price(s: Optional[str]) -> Optional[float]:
        """Return first numeric-looking price (handles commas and decimals)."""
        if not s:
            return None
        # normalize non-breaking spaces
        s = s.replace("\u00A0", " ")
        # find first number-like token: 1,234 or 1234.56 etc.
        m = re.search(r'(\d{1,3}(?:[,\d]*)(?:\.\d+)?)', s)
        if not m:
            return None
        num = m.group(1).replace(",", "")
        try:
            return float(num)
        except Exception:
            return None
