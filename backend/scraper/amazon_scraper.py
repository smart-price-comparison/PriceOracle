import aiohttp
import asyncio
from bs4 import BeautifulSoup
import random
from fuzzywuzzy import fuzz

# ----- SIMPLE UA ROTATION (no fake_useragent) -----
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B)"
]

def get_ua():
    return random.choice(UA_LIST)


async def amazon_scraper(user_input):
    results = []     # <--- REQUIRED: store items here

    search_query = user_input.strip().replace(" ", "+")
    url = f"https://www.amazon.in/s?k={search_query}"

    headers = {
        "User-Agent": get_ua(),
        "Accept-Language": "en-IN,en;q=0.9"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html_content = await response.text()
            await asyncio.sleep(random.uniform(1, 2))  

            soup = BeautifulSoup(html_content, 'lxml')
            products = soup.find_all("div", class_="sg-col-inner")

            for p in products:

                # name
                name_tag = p.find("h2", class_="a-size-medium")
                if not name_tag:
                    continue

                product_name = name_tag.get_text(strip=True)

                # fuzzy match
                score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
                if score < 85:
                    continue

                # image
                img_tag = p.find("img", class_="s-image")
                if img_tag:
                    image = img_tag.get("src") or img_tag.get("data-src")
                else:
                    image = None

                # product link
                a_tag = name_tag.find("a")
                product_link = None
                if a_tag and a_tag.get("href"):
                    product_link = "https://www.amazon.in" + a_tag["href"]

                # price (best-effort)
                price_tag = p.find("span", class_="a-offscreen")
                price_str = price_tag.get_text(strip=True) if price_tag else None

                # append final result
                results.append({
                    "name": product_name,
                    "image": image,
                    "url": product_link,
                    "price": price_str,
                    "score": score
                })

    return results   # <--- REQUIRED