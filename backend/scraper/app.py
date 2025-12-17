# filename: app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from amazon_scraper import amazon_scraper  # Imports the async function from scraper.py
from flipkart_scraper import flipkart_scraper
from myntra_scraper import myntra_scraper

app = Flask(__name__)
CORS(app)

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.json
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "No query provided"}), 400

        print(f"Searching for: {query}") # Debug print

        # Run the async scraper here. 
        # Since amazon_scraper is now an 'async def', this works perfectly.
        amazon_results = asyncio.run(amazon_scraper(query))
        flipkart_results = asyncio.run(flipkart_scraper(query))
        myntra_results = asyncio.run(myntra_scraper(query))

        all_results = {
            "amazon": amazon_results,
            "flipkart": flipkart_results,
            "myntra": myntra_results
        }

        return jsonify(all_results)

    except Exception as e:
        print("ERROR IN SCRAPER:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

