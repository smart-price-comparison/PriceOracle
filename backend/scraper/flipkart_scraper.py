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
FLIP_FUZZ_THRESHOLD = 70
MYNTRA_FUZZ_THRESHOLD = 65

# -------------------------
# Helpers
# -------------------------
def extract_price_from_card(card: Tag) -> Optional[str]:
    """Find first text in card that contains the Rupee symbol and digits."""
    for el in card.find_all(["div", "span", "p", "b", "strong"]):
        txt = (el.get_text(strip=True) or "")
        if "₹" in txt and re.search(r"\d", txt):
            return txt
    # fallback: search any text node
    for s in card.stripped_strings:
        if "₹" in s and re.search(r"\d", s):
            return s
    return None

def extract_title_from_product_link(link: Tag) -> str:
    """
    Heuristic: within the <a href*='/p/itm'> link, return the first
    non-empty text chunk after any <img> (the visible title).
    """
    # Prefer structured title tags if present
    possible_title = link.select_one("h1, h2, h3, span")
    if possible_title and possible_title.get_text(strip=True):
        return possible_title.get_text(strip=True)

    # Walk children: skip images and empty nodes, return first non-trivial text
    seen_img = False
    for child in link.descendants:
        if isinstance(child, Tag) and child.name == "img":
            seen_img = True
            continue
        if isinstance(child, NavigableString):
            text = child.strip()
            if not text:
                continue
            # Heuristic: skip short tokens like "Buy" or "Add"
            if len(text) < 3:
                continue
            # If we haven't seen an img yet, accept first meaningful text anyway
            return text
        if isinstance(child, Tag):
            txt = child.get_text(strip=True)
            if txt and (seen_img or len(txt) > 3):
                return txt
    # final fallback: full link text
    return link.get_text(" ", strip=True) or "Unknown Product"

def extract_image_from_card(card: Tag) -> Optional[str]:
    img = card.find("img")
    if not img:
        return None
    return img.get("data-src") or img.get("data-srcset") or img.get("src") or img.get("data-lazy")

# -------------------------
# Flipkart scraper (uses <a href*='/p/itm'> as product cards)
# -------------------------
async def flipkart_scraper(user_input: str, session: Optional[aiohttp.ClientSession] = None) -> List[ScrapedProduct]:
    results: List[ScrapedProduct] = []
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

        # SELECT product cards as anchor links containing product paths
        product_cards = soup.select("a[href*='/p/itm']")
        # If none found, fallback to previous container guesses
        if not product_cards:
            product_cards = soup.select("div._2QvvyD") or soup.find_all("div", {"data-id": True})

        for link in product_cards:
            # link may be <a> or a container with inner <a>
            if link.name != "a":
                link_tag = link.find("a", href=True)
                if not link_tag:
                    continue
                link = link_tag

            href = link.get("href")
            product_link = urljoin("https://www.flipkart.com", href) if href else None

            # Title extraction (heuristic)
            product_name = extract_title_from_product_link(link)

            # similarity check
            score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
            if score < FLIP_FUZZ_THRESHOLD:
                continue

            # price extraction (scan inside the anchor first, else card parent)
            price_str = extract_price_from_card(link)
            if not price_str:
                # sometimes price sits in parent container
                parent = link.parent
                price_str = extract_price_from_card(parent) if parent else None
            price_val = ScrapedProduct.clean_price(price_str) if price_str else None

            # image
            image_url = extract_image_from_card(link) or extract_image_from_card(link.parent) if link.parent else None

            # product id extraction
            m = re.search(r"/p/itm[^\s/]*?/([A-Za-z0-9_-]+)", product_link or "") or re.search(r"/([A-Za-z0-9]{8,})", product_link or "")
            product_id = m.group(1) if m else None

            results.append(ScrapedProduct(
                name=product_name,
                price=price_val,
                url=product_link,
                source="Flipkart",
                image_url=image_url,
                original_price=None,
                product_id=product_id
            ))

    except Exception:
        pass
    finally:
        if created:
            await session.close()

    return results

# -------------------------
# Myntra scraper (unchanged approach, kept robust)
# -------------------------
async def myntra_scraper(user_input: str, session: Optional[aiohttp.ClientSession] = None) -> List[ScrapedProduct]:
    results: List[ScrapedProduct] = []
    search_query = quote_plus(user_input.strip())
    url = f"https://www.myntra.com/search/{search_query}"

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
            await asyncio.sleep(random.uniform(1.5, 3.0))

        soup = BeautifulSoup(html, "lxml")

        product_cards = soup.find_all("li", class_="product-base") or soup.select("li")
        for card in product_cards:
            link_tag = card.find("a", href=True)
            if not link_tag:
                continue
            href = link_tag.get("href")
            product_link = urljoin("https://www.myntra.com", href) if href else None

            product_name = card.find("h3", class_="product-product")
            product_name = product_name.get_text(strip=True) if product_name else extract_title_from_product_link(link_tag)

            score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
            if score < MYNTRA_FUZZ_THRESHOLD:
                continue

            price_tag = card.find("span", class_="product-discountedPrice") or card.find("span", class_="product-price")
            price_str = price_tag.get_text(strip=True) if price_tag else extract_price_from_card(card)
            price_val = ScrapedProduct.clean_price(price_str) if price_str else None

            original_price_tag = card.find("span", class_="product-strike")
            original_price_str = original_price_tag.get_text(strip=True) if original_price_tag else None
            original_price_val = ScrapedProduct.clean_price(original_price_str) if original_price_str else None

            image_url = extract_image_from_card(card)

            m = re.search(r"/product/(\d+)", product_link or "") or re.search(r"-([0-9]{6,})", product_link or "")
            product_id = None
            if m:
                g = [g for g in m.groups() if g]
                product_id = g[-1] if g else None

            results.append(ScrapedProduct(
                name=product_name,
                price=price_val,
                url=product_link,
                source="Myntra",
                image_url=image_url,
                original_price=original_price_val,
                product_id=product_id
            ))

    except Exception:
        pass
    finally:
        if created:
            await session.close()

    return results

# -------------------------
# Optional runner
# -------------------------
async def scrape_both(query: str):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)) as session:
        fk = await flipkart_scraper(query, session=session)
        my = await myntra_scraper(query, session=session)
    return {"flipkart": fk, "myntra": my}
