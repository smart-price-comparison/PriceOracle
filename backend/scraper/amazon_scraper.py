from serpapi import GoogleSearch
import asyncio

async def amazon_scraper(query):
    try:
        params = {
            "engine": "amazon",
            "amazon_domain": "amazon.in",
            "k": query,               # ✅ use 'k', not 'keyword'
            "api_key": "dd8b1a22dcc45bab735a97e101ec4214381852698219d901f6b54b7438178b94"
        }

        # SerpAPI library is synchronous, so wrap in a thread executor
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: GoogleSearch(params).get_dict())

        if "error" in results:
            print("Error:", results["error"])
            return []

        products = results.get("organic_results", [])
        output = []

        for item in products:
            output.append({
                "name": item.get("title"),
                "price": item.get("price"),
                "image": item.get("thumbnail"),
                "link": item.get("link")
            })

        return output

    except Exception as e:
        print("Amazon scraper error:", e)
        return []

# 🔥 Optional test
if __name__ == "__main__":
    data = asyncio.run(amazon_scraper("iphone 13"))
    for p in data:
        print(p)



