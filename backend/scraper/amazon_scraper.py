# filename: backend/scraper/amazon_scraper.py
import os
import asyncio
import requests

SERPAPI_BASE = "https://serpapi.com/search.json"

async def amazon_scraper(query, pages=3):
    """
    Uses direct HTTP requests to SerpApi (no client library).
    Returns list of product dicts like before.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY environment variable is not set")

    all_products = []

    for page in range(1, pages + 1):
        try:
            params = {
                "engine": "amazon",
                "amazon_domain": "amazon.in",
                "k": query,
                "page": page,
                "api_key": api_key
            }
            # run blocking HTTP in thread to avoid blocking asyncio loop
            def do_request():
                r = requests.get(SERPAPI_BASE, params=params, timeout=30)
                r.raise_for_status()
                return r.json()

            results = await asyncio.to_thread(do_request)

            if "error" in results:
                print(f"Amazon page {page} error:", results["error"])
                break

            products = results.get("organic_results", []) or []
            if not products:
                break

            for item in products:
                all_products.append({
                    "name": item.get("title", ""),
                    "price": item.get("price", ""),
                    "image": item.get("thumbnail", ""),
                    "link": item.get("link", ""),
                    "rating": item.get("rating", ""),
                    "reviews": item.get("reviews", "")
                })

        except Exception as e:
            print(f"Error on page {page}:", e)
            continue

    return all_products
