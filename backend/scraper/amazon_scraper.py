import aiohttp
import asyncio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
from fuzzywuzzy import fuzz

ua = UserAgent()
async def amazon_scraper(user_input):
    search_query = user_input.strip().replace(" ", "+")
    url = f"https://www.amazon.in/s?k={search_query}"

    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html_content = await response.text()
            await asyncio.sleep(random.uniform(1, 3))  
            soup = BeautifulSoup(html_content, 'lxml')
            products =soup.find_all("div", class_="sg-col-inner")
            for p in products:
                name_tag=p.find("h2", class_="a-size-medium")
                if not(name_tag):
                     continue
                product_name=name_tag.get_text(strip=True)
                score = fuzz.partial_ratio(user_input.lower(), product_name.lower())
                if score >= 85:
                    img_tag = p.find("img", class_="s-image")
                    image = img_tag.get("src") or img_tag.get("data-src") if img_tag else "N/A"
                    a_tag = name_tag.find("a")
                    product_link = "https://www.amazon.in" + a_tag["href"] if a_tag and a_tag.get("href") else "N/A"

