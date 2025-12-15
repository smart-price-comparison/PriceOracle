import asyncio
import random
import re
from typing import List, Optional
from urllib.parse import quote_plus, urljoin

import aiohttp
from bs4 import BeautifulSoup, NavigableString, Tag
from fuzzywuzzy import fuzz

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
FLIP_FUZZ_THRESHOLD = 70

# -------------------------
# Helpers
# -------------------------
def extract_price_from_card(card: Tag) -> Optional[str]:
    for el in card.find_all(["div", "span", "p", "b", "strong"]):
        txt = (el.get_text(strip=True) or "")
        if "₹" in txt and re.search(r"\d", txt):
            return txt
    for s in card.stripped_strings:
        if "₹" in s and re.search(r"\d", s):
            return s
    return None

def extract_title_from_product_link(link: Tag) -> str:
    possible_title = link.select_one("h1, h2, h3, span")
    if possible_title and possible_title.get_text(strip=True):
        return possible_title.get_text(strip=True)
    seen_img = False
    for child in link.descendants:
        if isinstance(child, Tag) and child.name == "img":
            seen_img = True
            continue
        if isinstance(child, NavigableString):
            text = child.strip()
            if not text:
                continue
            if len(text) < 3:
                continue
            return text
        if isinstance(child, Tag):
            txt = child.get_text(strip=True)
            if txt and (seen_img or len(txt) > 3):
                return txt
    return link.get_text(" ", strip=True) or "Unknown Product"

def extract_image_from_card(card: Tag) -> Optional[str]:
    img = card.find("img")
    if not img:
        return None
    return img.get("data-src") or img.get("data-srcset") or img.get("src") or img.get("data-lazy")

def clean_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    m = re.search(r'[\d,]+', price_str.replace("₹", ""))
    return float(m.group(0).replace(",", "")) if m else None

# -------------------------
# Flipkart scraper (dict-based, fixed URLs)
# -------------------------
async def flipkart_scraper(user_input: str, session: Optional[aiohttp.ClientSession] = None) -> List[dict]:
    results: List[dict] = []
    search_query = quote_plus(user_input.strip())
    url = f"https://www.flipkart.com/search?q={search_query}"

    headers = {"User-Agent": get_ua(), "Accept-Language": "en-IN,en;q=0.9"}
    created = False
    if session is None:
        created = True
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT))

    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return results
            html = await resp.text()
            await asyncio.sleep(random.uniform(1.0, 2.5))

        soup = BeautifulSoup(html, "lxml")
        product_cards = soup.select("a[href*='/p/itm']") or soup.find_all("div", {"data-id": True})

        for link in product_cards:
            # If the element is not <a>, try to find inner <a>
            if link.name != "a":
                link_tag = link.find("a", href=True)
                if link_tag:
                    link = link_tag

            # ✅ Reliable URL extraction
            href = link.get("href") if link else None
            if not href and link.parent and link.parent.has_attr("data-id"):
                href = "/p/itm/" + link.parent["data-id"]

            product_link = urljoin("https://www.flipkart.com", href) if href else None

            product_name = extract_title_from_product_link(link)
            score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
            if score < FLIP_FUZZ_THRESHOLD:
                continue

            price_str = extract_price_from_card(link)
            if not price_str:
                parent = link.parent
                price_str = extract_price_from_card(parent) if parent else None
            price_val = clean_price(price_str) if price_str else None

            image_url = extract_image_from_card(link) or (extract_image_from_card(link.parent) if link.parent else None)

            m = re.search(r"/p/itm[^\s/]*?/([A-Za-z0-9_-]+)", product_link or "") or re.search(r"/([A-Za-z0-9]{8,})", product_link or "")
            product_id = m.group(1) if m else None

            results.append({
                "name": product_name,
                "price": price_val,
                "url": product_link,
                "image_url": image_url,
                "product_id": product_id,
                "source": "Flipkart"
            })

    except Exception as e:
        print("Flipkart scraper error:", e)
    finally:
        if created:
            await session.close()

    return results
