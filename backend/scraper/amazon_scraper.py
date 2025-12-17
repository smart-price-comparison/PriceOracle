# filename: scraper.py
import asyncio
from serpapi import GoogleSearch

# Rename this to be the main function we call
async def amazon_scraper(query, pages=3):
    all_products = []

    for page in range(1, pages + 1):
        try:
            params = {
                "engine": "amazon",
                "amazon_domain": "amazon.in",
                "k": query,
                "page": page,
                "api_key": "[REDACTED]" # Remember to replace this
            }

            search = GoogleSearch(params)
            
            # Run the blocking search in a separate thread so it doesn't block the loop
            results = await asyncio.to_thread(search.get_dict)

            if "error" in results:
                print(f"Amazon page {page} error:", results["error"])
                break

            products = results.get("organic_results", [])
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

