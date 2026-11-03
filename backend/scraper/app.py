import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.scraper.amazon_scraper import amazon_scraper
from backend.scraper.myntra_scraper import myntra_scraper
from backend.scraper.flipkart_scraper import flipkart_scraper

app = Flask(__name__)
CORS(app)

def to_dict(obj):
    """Convert SimpleNamespace to dict, otherwise return obj as-is."""
    if isinstance(obj, SimpleNamespace):
        return obj.__dict__
    return obj

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Request body must be a JSON object"}), 400

        query = data.get("query")
        if not isinstance(query, str):
            return jsonify({"error": "Query must be a string"}), 400
        query = query.strip()
        if not query:
            return jsonify({"error": "No query provided"}), 400

        print(f"Searching for: {query}")

        # ------------------------------
        # Run all scrapers in parallel
        # ------------------------------
        async def fetch_results():
            return await asyncio.gather(
                amazon_scraper(query),
                myntra_scraper(query),
                flipkart_scraper(query),
                return_exceptions=True,
            )

        raw_results = asyncio.run(fetch_results())
        marketplace_names = ("amazon", "myntra", "flipkart")
        results_by_marketplace = {}
        errors = {}
        for marketplace, result in zip(marketplace_names, raw_results):
            if isinstance(result, Exception):
                print(f"{marketplace.title()} scraper error:", result)
                errors[marketplace] = str(result)
                results_by_marketplace[marketplace] = []
            else:
                results_by_marketplace[marketplace] = result

        # ------------------------------
        # Convert to dict and ensure list
        # ------------------------------
        def clean_results(results):
            if results is None:
                return []
            return [to_dict(p) for p in results]

        amazon_results_dict = clean_results(results_by_marketplace["amazon"])
        myntra_results_dict = clean_results(results_by_marketplace["myntra"])
        flipkart_results_dict = clean_results(results_by_marketplace["flipkart"])

        # ------------------------------
        # Debug prints
        # ------------------------------
        print("Amazon sample:", amazon_results_dict[:3])
        print("Flipkart sample:", flipkart_results_dict[:3])
        print("Myntra sample:", myntra_results_dict[:3])

        # ------------------------------
        # Return JSON with UTF-8 support
        # ------------------------------
        return Response(
            json.dumps({
                "message": "Scraping completed",
                "results": {
                    "amazon": amazon_results_dict,
                    "flipkart": flipkart_results_dict,
                    "myntra": myntra_results_dict
                },
                "errors": errors,
            }, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        print("ERROR IN SCRAPER:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
