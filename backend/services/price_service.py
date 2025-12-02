# backend/services/price_service.py
"""
Orchestrates scraper calls and returns JSON-serializable results.

Expectations:
- flipkart scraper function: async def flipkart_scraper(query, ...) -> List[ScrapedProduct|dict|SimpleNamespace]
- myntra scraper function: async def myntra_scraper(query, ...) -> ...
- safe_amazon: def search_amazon_safe(query, ...) -> List[dict]
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List

from backend.core.logger import logger

# Use the real names from your scraper modules and alias them to the expected names
from backend.scraper.flipkart_scraper import flipkart_scraper as search_flipkart
from backend.scraper.myntra_scraper import myntra_scraper as search_myntra
from backend.scraper.safe_amazon import search_amazon_safe

# Optional DB fallback — import safely (database is top-level)
try:
    from database.connection import get_session
    from database.models import Product as DBProduct  # if you have a DB product model
    _DB_AVAILABLE = True
except Exception:
    _DB_AVAILABLE = False


# -------------------------
# Helpers
# -------------------------
def _serialize_item(item: Any) -> Dict[str, Any]:
    """
    Convert a ScrapedProduct / SimpleNamespace / dict into a plain dict:
    { title, price, link, image, source, product_id }
    """
    if item is None:
        return {}

    # If already a dict, normalize keys
    if isinstance(item, dict):
        return {
            "title": item.get("title") or item.get("name"),
            "price": item.get("price"),
            "link": item.get("link") or item.get("url"),
            "image": item.get("image") or item.get("image_url"),
            "source": item.get("source"),
            "product_id": item.get("product_id")
        }

    # Object with attributes (dataclass / SimpleNamespace / custom)
    title = getattr(item, "title", None) or getattr(item, "name", None)
    price = getattr(item, "price", None)
    link = getattr(item, "link", None) or getattr(item, "url", None)
    image = getattr(item, "image", None) or getattr(item, "image_url", None)
    source = getattr(item, "source", None)
    product_id = getattr(item, "product_id", None)

    return {
        "title": title,
        "price": price,
        "link": link,
        "image": image,
        "source": source,
        "product_id": product_id
    }


async def _maybe_await(func: Callable, *args, **kwargs):
    """
    Call `func(*args, **kwargs)`. If `func` is coroutine function, await it.
    If it's sync, run it in a threadpool so the event loop isn't blocked.
    """
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return await asyncio.to_thread(func, *args, **kwargs)


def _db_products(limit: int = 10) -> List[Dict[str, Any]]:
    """
    If a DB is available, return up to `limit` products as serialized dicts.
    Returns empty list if DB not configured.
    Time: O(k) where k=limit. Space: O(k).
    """
    if not _DB_AVAILABLE:
        return []

    session = get_session()
    try:
        rows = session.query(DBProduct).limit(limit).all()
        out = []
        for r in rows:
            # adapt if DBProduct fields differ
            out.append({
                "title": getattr(r, "title", None) or getattr(r, "name", None),
                "price": getattr(r, "price", None),
                "link": getattr(r, "link", None) or getattr(r, "url", None),
                "image": getattr(r, "image", None) or getattr(r, "image_url", None),
                "source": getattr(r, "source", None),
                "product_id": getattr(r, "id", None),
            })
        return out
    finally:
        session.close()


# -------------------------
# Public API
# -------------------------
async def get_all_prices(query: str, db_fallback_limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run all scrapers (concurrently) and return normalized results.

    Return JSON shape:
    {
        "flipkart": [...],
        "myntra": [...],
        "amazon": [...],
        # optional "fallback": [...] if scrapers returned nothing and DB fallback used
    }

    Complexity:
      - If scrapers run concurrently, time ≈ max(T_flipkart, T_myntra, T_amazon).
      - Space O(n) where n is total returned items.
    """
    # Start tasks concurrently (handles both async and sync scrapers)
    tasks = [
        _maybe_await(search_flipkart, query),
        _maybe_await(search_myntra, query),
        _maybe_await(search_amazon_safe, query),
    ]

    try:
        fk_res, my_res, am_res = await asyncio.gather(*tasks)
    except Exception as e:
        # If gather fails unexpectedly, attempt to collect partial results (best-effort)
        logger.exception("Error while running scrapers concurrently: %s", e)
        fk_res = my_res = am_res = []
        for fn in (search_flipkart, search_myntra, search_amazon_safe):
            try:
                res = await _maybe_await(fn, query)
            except Exception as ex:
                logger.warning("Scraper %s failed individually: %s", getattr(fn, "__name__", str(fn)), ex)
                res = []
            if fn is search_flipkart:
                fk_res = res
            elif fn is search_myntra:
                my_res = res
            else:
                am_res = res

    # Normalize and serialize results to plain dicts
    fk_list = [ _serialize_item(x) for x in (fk_res or []) ]
    my_list = [ _serialize_item(x) for x in (my_res or []) ]
    am_list = [ _serialize_item(x) for x in (am_res or []) ]

    # If everything is empty, try DB fallback (useful in dev)
    if not (fk_list or my_list or am_list):
        logger.info("No scraper results for query '%s' — attempting DB fallback", query)
        fallback = _db_products(limit=db_fallback_limit)
        return {"flipkart": [], "myntra": [], "amazon": [], "fallback": fallback}

    return {"flipkart": fk_list, "myntra": my_list, "amazon": am_list}
