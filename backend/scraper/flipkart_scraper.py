import asyncio
from serpapi import GoogleSearch

from backend.core.config import get_serpapi_api_key

async def flipkart_scraper(query, pages=2):
    all_products = []
    api_key = get_serpapi_api_key()

    for page in range(pages):
        try:
            params = {
                "engine": "google",
                "q": f"site:flipkart.com {query}",
                "gl": "in",
                "hl": "en",
                "start": page * 10,
                "api_key": api_key,
            }

            search = GoogleSearch(params)
            results = await asyncio.to_thread(search.get_dict)

            if "error" in results:
                print(f"Flipkart page {page} error:", results["error"])
                break

            for item in results.get("organic_results", []):
                link = item.get("link")
                title = item.get("title")
                thumbnail = item.get("thumbnail")

                if not link or not title:
                    continue

                # OPTIONAL: enable for stricter product-only results
                # if "/p/" not in link:
                #     continue

                all_products.append({
                    "name": title,
                    "price": None,
                    "url": link,
                    "image_url": thumbnail,  # ✅ REAL IMAGE URL
                    "source": "Flipkart"
                })

        except Exception as e:
            print(f"Flipkart scraper error on page {page}:", e)

    if not all_products:
        print("No Flipkart products found for:", query)

    return all_products
