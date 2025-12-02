# filename: scraper_to_db.py
import asyncio
from db_utils_sqlite import init_db, insert_product

# import the async scraper from amazon_scraper.py
from amazon_scraper import amazon_scraper

async def run_and_store(query, pages=2):
    """
    Run the amazon_scraper, insert results into SQLite DB and print a confirmation.
    Returns the raw results list.
    """
    init_db()
    results = await amazon_scraper(query, pages=pages)
    if not results:
        print("Scraper returned no results.")
        return results

    inserted = 0
    for r in results:
        name = r.get("name") or ""
        price = r.get("price") or ""
        url = r.get("link") or ""
        image = r.get("image") or ""
        try:
            insert_product(name, price, url, image, source="amazon")
            inserted += 1
        except Exception as e:
            print("DB insert error for item:", name, e)

    print(f"Scraper returned {len(results)} items, inserted {inserted} into DB.")
    return results

# quick runner for manual tests
if __name__ == "__main__":
    q = input("Query: ").strip() or "nike shoes"
    asyncio.run(run_and_store(q, pages=1))
