# test_run.py
import asyncio
import aiohttp
from typing import Any

# import scrapers from package path
from backend.scraper.flipkart_scraper import flipkart_scraper
from backend.scraper.myntra_scraper import myntra_scraper
from backend.scraper.amazon_scraper import amazon_scraper
# if you want to test amazon too:
# from backend.scraper.amazon_scraper import amazon_scraper

QUERY = "nike shoes"
TOP_N = 5
DEFAULT_TIMEOUT = 20


def print_product(i: int, p: Any) -> None:
    # adapt to your ScrapedProduct fields
    name = getattr(p, "name", None) or getattr(p, "title", None) or "N/A"
    price = getattr(p, "price", None)
    pid = getattr(p, "product_id", None)
    url = getattr(p, "url", None) or getattr(p, "link", None) or "N/A"
    img = getattr(p, "image_url", None) or getattr(p, "image", None) or "N/A"
    print(f"{i}. {name[:120]} | price: {price} | id: {pid} | url: {url} | img: {bool(img)}")


async def main():
    q = QUERY
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)) as session:
        print(f"\n== Flipkart results for: '{q}' ==\n")
        try:
            fk_results = await flipkart_scraper(q, session=session)
        except Exception as e:
            print("Flipkart scraper error:", e)
            fk_results = []
        if not fk_results:
            print("No Flipkart results found.")
        for i, p in enumerate(fk_results[:TOP_N], start=1):
            print_product(i, p)

        print(f"\n== Myntra results for: '{q}' ==\n")
        try:
            my_results = await myntra_scraper(q, session=session)
        except Exception as e:
            print("Myntra scraper error:", e)
            my_results = []
        if not my_results:
            print("No Myntra results found.")
        for i, p in enumerate(my_results[:TOP_N], start=1):
            print_product(i, p)
        print(f"\n== Amazon results for: '{q}' ==\n")
        try:
            am_results = await amazon_scraper(q)
        except Exception as e:
            print("Amazon scraper error:", e)
            am_results = []
        if not am_results:
            print("No Amazon results found.")
        for i, p in enumerate(am_results[:TOP_N], start=1):
            print_product(i, p)
        # optional: test amazon if available
        # print(f"\n== Amazon results for: '{q}' ==\n")
        # try:
        #     am_results = await amazon_scraper(q, session=session)
        # except Exception as e:
        #     print("Amazon scraper error:", e)
        #     am_results = []
        # for i, p in enumerate(am_results[:TOP_N], start=1):
        #     print_product(i, p)


if __name__ == "__main__":
    asyncio.run(main())
  