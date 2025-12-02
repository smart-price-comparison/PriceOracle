import time
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.amazon.in/"
}

def _parse_search_html(html):
    """Resilient Amazon HTML parsing."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    containers = soup.select("div.s-result-item[data-asin]") or soup.select("div[data-asin]")

    for item in containers:
        asin = item.get("data-asin") or None

        # TITLE extraction attempts
        title = None
        title_selectors = [
            "h2 a span",
            "span.a-size-base-plus",
            "span.a-size-medium",
            "a[aria-label]",
            "h2 a"
        ]
        for sel in title_selectors:
            tag = item.select_one(sel)
            if tag:
                if tag.name == "a":
                    title = tag.get("aria-label") or tag.get_text(strip=True)
                else:
                    title = tag.get_text(strip=True)
                if title:
                    break

        # fallback title from image alt
        if not title:
            img_tag = item.select_one("img")
            if img_tag:
                alt = img_tag.get("alt")
                if alt:
                    title = alt.strip()

        # PRICE extraction
        price = None
        price_tag = item.select_one(".a-offscreen") or item.select_one(".a-price-whole")
        if price_tag:
            price = price_tag.get_text(strip=True)

        # fallback price combo
        if not price:
            pw = item.select_one(".a-price-whole")
            pf = item.select_one(".a-price-fraction")
            if pw:
                price = pw.get_text(strip=True) + (pf.get_text(strip=True) if pf else "")

        # URL extraction
        url = None
        url_tag = item.select_one("h2 a") or item.select_one("a.a-link-normal[href]") or item.select_one("a[aria-label][href]")
        if url_tag and url_tag.get("href"):
            href = url_tag.get("href")
            if href.startswith("/"):
                url = f"https://www.amazon.in{href}"
            else:
                url = href

        # image url
        img_url = None
        img_tag = item.select_one("img")
        if img_tag:
            img_url = img_tag.get("src") or img_tag.get("data-src")

        # skip empty containers
        if not title and not asin and not price:
            continue

        results.append({
            "asin": asin,
            "title": title,
            "name": title,
            "price": price,
            "url": url,
            "image_url": img_url
        })

    return results


def search_amazon_safe(query: str, max_retries: int = 2, timeout: int = 10):
    """
    Safe Amazon search wrapper.
    Returns [] if blocked, if markup missing, or anything fails.
    """
    q = quote(query)
    url = f"https://www.amazon.in/s?k={q}"
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    backoff = 1
    for attempt in range(1, max_retries + 1):
        try:
            r = session.get(url, timeout=timeout)
        except Exception as e:
            print(f"[amazon-safe] network error attempt {attempt}: {e}")
            time.sleep(backoff)
            backoff *= 2
            continue

        if r.status_code != 200:
            print(f"[amazon-safe] status {r.status_code} on attempt {attempt}; giving up.")
            return []

        html = r.text.lower()

        # detect captcha / block
        if ("captcha" in html) or ("unusual traffic" in html) or ("enable javascript" in html):
            print(f"[amazon-safe] detected bot-block or captcha on attempt {attempt}; giving up.")
            return []

        # parse actual results
        results = _parse_search_html(r.text)
        if results:
            return results

        print(f"[amazon-safe] no product containers found on attempt {attempt}. retrying...")
        time.sleep(backoff)
        backoff *= 2

    print("[amazon-safe] final fallback -> returning empty list.")
    return []
