from serpapi import GoogleSearch
import asyncio

async def amazon_scraper(query, pages=3):   # ⭐ CHANGE: Added page count
    try:
        loop = asyncio.get_event_loop()
        all_products = []

        for page in range(1, pages + 1):    # ⭐ CHANGE: Loop through pages
            params = {
                "engine": "amazon",
                "amazon_domain": "amazon.in",
                "k": query,
                "page": page,               # ⭐ CHANGE: Enable pagination
                "api_key": "[REDACTED]"
            }

            results = await loop.run_in_executor(
                None,
                lambda: GoogleSearch(params).get_dict()
            )

            if "error" in results:
                print(f"Amazon page {page} error:", results["error"])
                break

            products = results.get("organic_results", [])
            if not products:
                break

            # ⭐ CHANGE: cleaner extraction
            for item in products:
                all_products.append({
                    "name": item.get("title"),
                    "price": item.get("price"),
                    "image": item.get("thumbnail"),
                    "link": item.get("link"),
                    "rating": item.get("rating"),
                    "reviews": item.get("reviews")
                })

        return all_products

    except Exception as e:
        print("Amazon scraper error:", e)
        return []

# Test
if __name__ == "__main__":
    data = asyncio.run(amazon_scraper("iphone 13"))
    print(f"Total results: {len(data)}")
    for p in data:
        print(p)

