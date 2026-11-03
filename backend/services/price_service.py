import asyncio
from types import SimpleNamespace
from backend.scraper.amazon_scraper import amazon_scraper
from backend.scraper.flipkart_scraper import flipkart_scraper
from backend.scraper.myntra_scraper import myntra_scraper

async def get_all_prices(query: str):
    flipkart_results, myntra_results, amazon_results = await asyncio.gather(
        flipkart_scraper(query),
        myntra_scraper(query),
        amazon_scraper(query),
    )

    return {
        "flipkart": flipkart_results or [],
        "myntra": [
            vars(product) if isinstance(product, SimpleNamespace) else product
            for product in (myntra_results or [])
        ],
        "amazon": amazon_results or [],
    }
