# amazon_check_containers.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

url = "https://www.amazon.in/s?k=" + quote("nike shoes")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9"
}

r = requests.get(url, headers=headers, timeout=15)
print("Status:", r.status_code)
html = r.text

# save full html so you can open it visually
with open("amazon_full.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved amazon_full.html (open it in a browser to inspect visually).")

# parse and count common product markers
soup = BeautifulSoup(html, "html.parser")
count_data_asin = len(soup.select("div[data-asin]"))
count_s_result = len(soup.select("div.s-result-item"))
count_price_offscreen = len(soup.select(".a-offscreen"))
count_price_whole = len(soup.select(".a-price-whole"))

print("Counts found:")
print("  div[data-asin]:", count_data_asin)
print("  div.s-result-item:", count_s_result)
print("  .a-offscreen (alt price nodes):", count_price_offscreen)
print("  .a-price-whole:", count_price_whole)

# show a sample snippet of the first product container if present
first = soup.select_one("div[data-asin]") or soup.select_one("div.s-result-item")
if first:
    snippet = first.prettify()[:1000]
    print("\nSample product container (first 1000 chars):\n")
    print(snippet)
else:
    print("\nNo product containers found with common selectors.")
    print("If none found, the page may be JS-rendered or Amazon changed markup.")
