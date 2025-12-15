# filename: app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from amazon_scraper import amazon_scraper
from myntra_scraper import myntra_scraper
from flipkart_scraper import flipkart_scraper
from types import SimpleNamespace  # ✅ ADDED to handle SimpleNamespace conversion

app = Flask(__name__)
CORS(app)

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "No query provided"}), 400

        print(f"Searching for: {query}")

        # ✅ RUN ASYNC SCRAPERS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        amazon_results = loop.run_until_complete(amazon_scraper(query))
        myntra_results = loop.run_until_complete(myntra_scraper(query))
        flipkart_results = loop.run_until_complete(flipkart_scraper(query))
        loop.close()

        # ✅ CONVERT SimpleNamespace TO dict FOR JSON SERIALIZATION
        def to_dict(obj):
            if isinstance(obj, SimpleNamespace):
                return obj.__dict__  # ✅ key change
            return obj

        amazon_results_dict = [to_dict(p) for p in amazon_results]  # ✅ changed
        myntra_results_dict = [to_dict(p) for p in myntra_results] 
        flipkart_results_dict = [to_dict(p) for p in flipkart_results] # ✅ changed

        return jsonify({
            "message": "Scraping completed",
            "results": {
                "amazon": amazon_results_dict,  # ✅ changed
                "myntra": myntra_results_dict,
                "flipkart":flipkart_results_dict  # ✅ changed
            }
        })

    except Exception as e:
        print("ERROR IN SCRAPER:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

