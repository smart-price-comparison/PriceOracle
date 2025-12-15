# backend/scraper/myntra_scraper.py
# Async-compatible Myntra scraper for use with your test_run.py
#
# Requirements:
#   pip install aiohttp beautifulsoup4 selenium webdriver-manager

from typing import List, Optional
import asyncio
import re
from types import SimpleNamespace
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# optional Selenium imports only used if we fall back
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    webdriver = None  # Selenium not available; fallback disabled

import aiohttp

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _parse_price(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    m = re.search(r'[\d,]+', text.replace("\u20b9", ""))
    return m.group(0).replace(",", "") if m else None


def _make_obj_from_dict(d: dict) -> SimpleNamespace:
    return SimpleNamespace(
        name=d.get("name"),
        title=d.get("name"),
        price=d.get("price"),
        product_id=d.get("product_id"),
        url=d.get("url"),
        link=d.get("url"),
        image_url=d.get("image_url"),
        image=d.get("image_url"),
        rating=d.get("rating"),
    )


async def _aiohttp_fetch_parse(url: str, session: aiohttp.ClientSession, product_card_selector: str = ".product-base", top_n: Optional[int] = None) -> List[SimpleNamespace]:
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept-Language": "en-IN,en;q=0.9",
    }
    async with session.get(url, headers=headers) as resp:
        text = await resp.text()
    soup = BeautifulSoup(text, "html.parser")

    selectors = [
        product_card_selector,
        "li.product-grid__item",
        ".product.product-base",
        "li.search-result, li.product",
        "a[href*='/product']"
    ]

    cards = []
    for sel in selectors:
        cards = soup.select(sel)
        if cards:
            break

    results = []
    seen = set()
    for card in cards[:top_n] if top_n else cards:
        a = card.find("a", href=True)
        href = a["href"] if a else None

        # ✅ Fix relative URL
        url_abs = urljoin("https://www.myntra.com", href) if href else None
        if url_abs and url_abs in seen:
            continue
        if url_abs:
            seen.add(url_abs)

        img = card.find("img")
        # ✅ Fix image extraction
        image_url = None
        if img:
            image_url = img.get("src") or img.get("data-src") or img.get("data-srcset")

        name = img.get("alt") if img and img.get("alt") else (card.get_text(strip=True)[:200] or None)

        price_el = card.select_one(".product-discountedPrice, .product-price, .product-discountPrice")
        price = _parse_price(price_el.get_text()) if price_el else None
        if not price:
            m = re.search(r'₹\s*[\d,]+|[\d,]{2,}', card.get_text(" "))
            price = _parse_price(m.group(0)) if m else None

        rating_el = card.select_one(".product-rating, .rating")
        rating = rating_el.get_text().strip() if rating_el else None

        results.append(_make_obj_from_dict({
            "name": name,
            "price": price,
            "url": url_abs,
            "image_url": image_url,
            "rating": rating,
        }))

    return results


def _start_selenium_driver(headless: bool = True):
    if webdriver is None:
        raise RuntimeError("Selenium is not installed or failed to import.")
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"user-agent={DEFAULT_USER_AGENT}")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)
    return driver


def _selenium_scrape(url: str, headless: bool = True, wait: int = 3, product_card_selector: str = ".product-base", max_products: Optional[int] = None) -> List[SimpleNamespace]:
    driver = _start_selenium_driver(headless=headless)
    try:
        driver.get(url)
        import time
        time.sleep(wait)

        cards = driver.find_elements(By.CSS_SELECTOR, product_card_selector) if hasattr(driver, "find_elements") else []
        if not cards:
            cards = driver.find_elements(By.XPATH, "//a[contains(@href,'/product') or contains(@href,'-p-')]")

        results = []
        seen = set()
        for card in cards:
            if max_products and len(results) >= max_products:
                break
            try:
                html = card.get_attribute("outerHTML")
            except Exception:
                continue
            soup = BeautifulSoup(html, "html.parser")
            a = soup.find("a", href=True)
            href = a["href"] if a else None

            # ✅ Fix relative URL
            product_url = urljoin("https://www.myntra.com", href) if href else None
            if product_url and product_url in seen:
                continue
            if product_url:
                seen.add(product_url)

            img = soup.find("img")
            # ✅ Fix image
            image_url = None
            if img:
                image_url = img.get("src") or img.get("data-src") or img.get("data-srcset")

            name = img.get("alt") if img and img.get("alt") else (soup.get_text(" ").strip()[:200] or None)

            price_el = soup.select_one(".product-discountedPrice, .product-price, .product-discountPrice")
            price = _parse_price(price_el.get_text()) if price_el else None
            if not price:
                m = re.search(r'₹\s*[\d,]+|[\d,]{2,}', soup.get_text(" "))
                price = _parse_price(m.group(0)) if m else None

            rating_el = soup.select_one(".product-rating, .rating")
            rating = rating_el.get_text().strip() if rating_el else None

            results.append(_make_obj_from_dict({
                "name": name,
                "price": price,
                "url": product_url,
                "image_url": image_url,
                "rating": rating,
            }))

        return results
    finally:
        try:
            driver.quit()
        except Exception:
            pass


async def myntra_scraper(
    query: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None,
    url: Optional[str] = None,
    top_n: int = 20,
    headless: bool = True,
    wait: int = 3,
    product_card_selector: str = ".product-base",
    max_products: Optional[int] = None,
) -> List[SimpleNamespace]:
    if url is None and query is None:
        raise ValueError("Either 'query' or 'url' must be provided.")

    if url is None:
        from urllib.parse import quote_plus
        raw = quote_plus(query)
        url = f"https://www.myntra.com/{raw.replace('+', '-')}" + f"?rawQuery={raw}"

    results = []
    if session is not None:
        try:
            results = await _aiohttp_fetch_parse(url, session=session, product_card_selector=product_card_selector, top_n=top_n)
        except Exception:
            results = []
        if results:
            return results[:max_products] if max_products else results[:top_n]

    loop = asyncio.get_running_loop()
    try:
        scraped = await loop.run_in_executor(None, _selenium_scrape, url, headless, wait, product_card_selector, max_products or top_n)
        return scraped[:max_products] if max_products else scraped[:top_n]
    except Exception:
        return []


def scrape_myntra_sync(*args, **kwargs):
    return _selenium_scrape(*args, **kwargs)
