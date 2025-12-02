# backend/services/price_service.py
from scraper.flipkart_scraper import search_flipkart  # your existing functions
from scraper.myntra_scraper import search_myntra
from scraper.safe_amazon import search_amazon_safe

async def get_all_prices(query: str):
    # If your scrapers are sync, you can call them directly; if they are async, await them.
    fk = search_flipkart(query)      # returns list
    my = search_myntra(query)        # returns list
    am = search_amazon_safe(query)   # safe wrapper -> returns list or []
    return {
        "flipkart": fk or [],
        "myntra": my or [],
        "amazon": am or []
    }
