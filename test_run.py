import asyncio
import aiohttp
import json

# async scrapers (keep as-is)
from backend.scraper.flipkart_scraper import flipkart_scraper
from backend.scraper.myntra_scraper import myntra_scraper

# safe Amazon wrapper (sync) that returns [] on failure
from backend.scraper.safe_amazon import search_amazon_safe

QUERY = "puma shoes"
TOP_N = 5
DEFAULT_TIMEOUT = 20


def print_product_dict(i: int, p: dict) -> None:
    """Safe printing for dict-like product output."""
    name = p.get("name") or p.get("title") or "N/A"
    price = p.get("price") or p.get("price_text") or "N/A"
    # normalize rupee sign for console readability
    if isinstance(price, str):
        price = price.replace("\u20b9", "Rs.")
    pid = p.get("product_id") or p.get("asin") or p.get("id")
    url = p.get("url") or p.get("link") or "N/A"
    img = p.get("image_url") or p.get("image") or "N/A"
    print(f"{i}. {name[:120]} | price: {price} | id: {pid} | url: {url} | img: {bool(img)}")


async def main():
    q = QUERY
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)) as session:
        # FLIPKART
        print(f"\n== Flipkart results for: '{q}' ==\n")
        try:
            fk_results = await flipkart_scraper(q)
        except Exception as e:
            print("Flipkart scraper error:", e)
            fk_results = []
        if not fk_results:
            print("No Flipkart results found.")
        for i, p in enumerate(fk_results[:TOP_N], start=1):
            # if scraper returns objects, try attribute fallbacks
            if isinstance(p, dict):
                print_product_dict(i, p)
            else:
                # try object-like
                print_product_dict(i, {
                    "name": getattr(p, "name", None) or getattr(p, "title", None),
                    "price": getattr(p, "price", None),
                    "product_id": getattr(p, "product_id", None),
                    "url": getattr(p, "url", None) or getattr(p, "link", None),
                    "image": getattr(p, "image_url", None) or getattr(p, "image", None)
                })

        # MYNTRA
        print(f"\n== Myntra results for: '{q}' ==\n")
        try:
            my_results = await myntra_scraper(q, session=session)
        except Exception as e:
            print("Myntra scraper error:", e)
            my_results = []
        if not my_results:
            print("No Myntra results found.")
        for i, p in enumerate(my_results[:TOP_N], start=1):
            if isinstance(p, dict):
                print_product_dict(i, p)
            else:
                print_product_dict(i, {
                    "name": getattr(p, "name", None) or getattr(p, "title", None),
                    "price": getattr(p, "price", None),
                    "product_id": getattr(p, "product_id", None),
                    "url": getattr(p, "url", None) or getattr(p, "link", None),
                    "image": getattr(p, "image_url", None) or getattr(p, "image", None)
                })

        # AMAZON (safe, non-blocking)
        print(f"\n== Amazon results for: '{q}' ==\n")
        try:
            # search_amazon_safe is sync, run in a thread to avoid blocking the event loop
            am_results = await asyncio.to_thread(search_amazon_safe, q)
        except Exception as e:
            print("Amazon scraper error:", e)
            am_results = []

        if not am_results:
            print("No Amazon results found.")

        for i, p in enumerate(am_results[:TOP_N], start=1):
            # amazon wrapper returns dicts; be defensive
            if isinstance(p, dict):
                print_product_dict(i, p)
            else:
                print_product_dict(i, {
                    "name": getattr(p, "name", None) or getattr(p, "title", None),
                    "price": getattr(p, "price", None),
                    "product_id": getattr(p, "product_id", None),
                    "url": getattr(p, "url", None) or getattr(p, "link", None),
                    "image": getattr(p, "image_url", None) or getattr(p, "image", None)
                })

    # Optional: print a compact JSON summary for frontend testing (runs AFTER scrapers)
    def normalize_product(p):
        """Return a plain dict for dict-like or object-like scraped products."""
        if p is None:
            return {}
        if isinstance(p, dict):
            return p
        # object-like: try common attributes
        try:
            return {
                "name": getattr(p, "name", None) or getattr(p, "title", None),
                "price": getattr(p, "price", None) or getattr(p, "price_text", None),
                "product_id": getattr(p, "product_id", None) or getattr(p, "asin", None) or getattr(p, "id", None),
                "url": getattr(p, "url", None) or getattr(p, "link", None),
                "image": getattr(p, "image_url", None) or getattr(p, "image", None)
            }
        except Exception:
            # fallback: return string repr so json.dumps won't fail
            return {"repr": str(p)}

    summary = {
        "flipkart": [normalize_product(x) for x in (fk_results or [])],
        "myntra": [normalize_product(x) for x in (my_results or [])],
        "amazon": [normalize_product(x) for x in (am_results or [])],
    }

    # pretty-print a truncated JSON summary (safe)
    json_out = json.dumps(summary, indent=2, ensure_ascii=False)
    print("\n== JSON Summary (compact) ==\n")
    print(json_out[:2000])  # keep console-friendly size


if __name__ == "__main__":
    asyncio.run(main())
    