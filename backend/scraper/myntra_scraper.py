# myntra_scraper.py
import asyncio
import random
import re
from typing import List, Optional
from urllib.parse import quote_plus, urljoin

import aiohttp
from bs4 import BeautifulSoup, NavigableString, Tag
from fuzzywuzzy import fuzz

from database.models import ScrapedProduct

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B)"
]

def get_ua():
    return random.choice(UA_LIST)
DEFAULT_TIMEOUT = 12
MYNTRA_FUZZ_THRESHOLD = 65

# -------------------------
# Helpers
# -------------------------
def extract_price_from_card(card: Tag) -> Optional[str]:
    """Find first text in card that looks like a price with Rs/₹ and digits."""
    for el in card.find_all(["div", "span", "p", "b", "strong"]):
        txt = (el.get_text(strip=True) or "")
        if ("₹" in txt or "Rs" in txt or "rs" in txt) and re.search(r"\d", txt):
            return txt
    for s in card.stripped_strings:
        if ("₹" in s or "Rs" in s or "rs" in s) and re.search(r"\d", s):
            return s
    return None

def extract_title_from_link(link: Tag) -> str:
    """Take first meaningful heading/text inside the product link."""
    # Prefer heading tags (h1/h2/h3) if present
    heading = link.find(["h1", "h2", "h3"])
    if heading and heading.get_text(strip=True):
        return heading.get_text(strip=True)

    seen_img = False
    for child in link.descendants:
        if isinstance(child, Tag) and child.name == "img":
            seen_img = True
            continue
        if isinstance(child, NavigableString):
            text = child.strip()
            if not text or len(text) < 3:
                continue
            return text
        if isinstance(child, Tag):
            txt = child.get_text(strip=True)
            if txt and (seen_img or len(txt) > 3):
                return txt

    return link.get_text(" ", strip=True) or "Unknown Product"

def extract_image_from_card(card: Tag) -> Optional[str]:
    """Handle lazy-loaded Myntra images."""
    img = card.find("img")
    if not img:
        return None
    return (
        img.get("data-src")
        or img.get("data-srcset")
        or img.get("src")
        or img.get("data-lazy")
    )

# -------------------------
# Myntra scraper
# -------------------------
async def myntra_scraper(
    user_input: str,
    session: Optional[aiohttp.ClientSession] = None
) -> List[ScrapedProduct]:
    results: List[ScrapedProduct] = []

    search_query = quote_plus(user_input.strip())
    url = f"https://www.myntra.com/search/{search_query}"

    headers = {
        "User-Agent": get_ua(),
        "Accept-Language": "en-IN,en;q=0.9",
    }

    created = False
    if session is None:
        created = True
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        )

    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return results
            html = await resp.text()
            await asyncio.sleep(random.uniform(1.5, 3.0))

        soup = BeautifulSoup(html, "lxml")

        # New structure: products are <li id="...">
        product_cards = soup.find_all("li", id=True)

        for card in product_cards:
            # link
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue

            href = link_tag.get("href")
            product_link = urljoin("https://www.myntra.com", href) if href else None

            # name
            product_name = extract_title_from_link(link_tag)

            # fuzzy
            score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
            if score < MYNTRA_FUZZ_THRESHOLD:
                continue

            # price (generic Rs/₹ detection)
            price_str = extract_price_from_card(card)
            price_val = ScrapedProduct.clean_price(price_str) if price_str else None

            # original price (try to grab a second price if present)
            original_price_val = None
            original_price_str = None
            all_prices = []
            for el in card.find_all(["div", "span", "p", "b", "strong"]):
                t = (el.get_text(strip=True) or "")
                if ("₹" in t or "Rs" in t or "rs" in t) and re.search(r"\d", t):
                    all_prices.append(t)
            if len(all_prices) > 1:
                original_price_str = all_prices[1]
                original_price_val = ScrapedProduct.clean_price(original_price_str)

            # image (lazy loading)
            image_url = extract_image_from_card(card)

            # product id (from li id or URL)
            product_id = card.get("id")
            if not product_id and product_link:
                m = re.search(r"/product/(\d+)", product_link) or re.search(
                    r"-([0-9]{6,})", product_link
                )
                if m:
                    g = [g for g in m.groups() if g]
                    product_id = g[-1] if g else None

            results.append(
                ScrapedProduct(
                    name=product_name,
                    price=price_val,
                    url=product_link,
                    source="Myntra",
                    image_url=image_url,
                    original_price=original_price_val,
                    product_id=product_id,
                )
            )

    except Exception:
        pass
    finally:
        if created:
            await session.close()

    return results

# quick test (optional)
if __name__ == "__main__":
    async def run():
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        ) as s:
            res = await myntra_scraper("nike shoes", session=s)
            for r in res[:5]:
                print(r.name, r.price, r.url)
    asyncio.run(run())
