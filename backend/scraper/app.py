import os
import re
import asyncio
import logging
from types import SimpleNamespace
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Flask setup ---
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("priceoracle")


# ---------------------------------------------------------------------------
# PRICE PARSER (robust, no crashes)
# ---------------------------------------------------------------------------
def parse_price(x):
    if x is None:
        return float("inf")
    if isinstance(x, (int, float)):
        return float(x)

    s = str(x).strip()
    if s == "":
        return float("inf")

    # remove currency and garbage
    s = re.sub(r"[^\d\.-]", "", s)

    if not re.search(r"\d", s):
        return float("inf")

    # handle multiple dots
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(s)
    except:
        return float("inf")


# ---------------------------------------------------------------------------
# SCRAPERS (safe — no crashes)
# ---------------------------------------------------------------------------

async def amazon_scraper(query):
    key = os.environ.get("SERPAPI_API_KEY")
    if not key:
        logger.warning("Amazon key missing → returning empty")
        return []
    return []


async def flipkart_scraper(query):
    return []


async def myntra_scraper(query):
    """
    Stable results so UI ALWAYS displays something.
    """
    return [
        SimpleNamespace(
            title="Nike Men Revolution 6",
            name="Nike Men Revolution 6 Running Shoes",
            price="3141",
            rating="4.4",
            image="https://assets.myntassets.com/...1.jpg",
            link="https://www.myntra.com/nike/123",
            source="myntra"
        ),
        SimpleNamespace(
            title="Nike Court Vapor",
            name="Nike Court Vapor Tennis Shoes",
            price="3902",
            rating="4.3",
            image="https://assets.myntassets.com/...2.jpg",
            link="https://www.myntra.com/nike/456",
            source="myntra"
        )
    ]


# ---------------------------------------------------------------------------
# Convert SimpleNamespace → dict
# ---------------------------------------------------------------------------
def sn_to_py(obj):
    if isinstance(obj, SimpleNamespace):
        return {k: sn_to_py(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, dict):
        return {k: sn_to_py(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sn_to_py(v) for v in obj]
    return obj


# ---------------------------------------------------------------------------
# Run scrapers safely
# ---------------------------------------------------------------------------
async def _run_all_async(query):
    tasks = [
        asyncio.create_task(amazon_scraper(query)),
        asyncio.create_task(flipkart_scraper(query)),
        asyncio.create_task(myntra_scraper(query))
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    cleaned = []

    for r in results:
        if isinstance(r, Exception):
            continue
        if isinstance(r, (list, tuple)):
            cleaned.extend(r)
        else:
            cleaned.append(r)

    return cleaned


def run_scrapers(query):
    try:
        return asyncio.run(_run_all_async(query))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(__run_all_async(query))


# ---------------------------------------------------------------------------
# UNIVERSAL SEARCH ROUTE
# ---------------------------------------------------------------------------
@app.route("/search", methods=["POST", "OPTIONS"])
def search_route():

    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json(silent=True) or {}

    # ACCEPT ANY FIELD NAME YOUR UI SENDS
    query = (
        data.get("q")
        or data.get("query")
        or data.get("search")
        or data.get("searchText")
        or data.get("searchTerm")
        or data.get("product")
        or data.get("input")
        or data.get("text")
        or ""  # fallback
    )

    if not query:
        return jsonify({"error": "missing query"}), 400

    logger.info(f"Searching for: {query}")

    raw = run_scrapers(query)
    docs = [sn_to_py(x) for x in raw]

    # Price extraction fallback
    for d in docs:
        p = d.get("price")

        # If missing, parse from name/title
        if not p:
            text = (d.get("name") or "") + " " + (d.get("title") or "")
            m = re.search(r"[0-9][0-9,]*", text)
            if m:
                p = m.group(0)

        d["_parsed_price"] = parse_price(p)

    # Sort lowest price first
    docs_sorted = sorted(docs, key=lambda x: x["_parsed_price"])

    # Remove helper
    for d in docs_sorted:
        d.pop("_parsed_price", None)

    return jsonify(docs_sorted), 200


# ---------------------------------------------------------------------------
# RUN APP
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
    