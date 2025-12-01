async def get_all_prices(product_name: str):
    # Mock data to test route
    return [
        {"store": "Amazon", "price": "₹50,000", "link": "https://amazon.com/example"},
        {"store": "Flipkart", "price": "₹49,500", "link": "https://flipkart.com/example"},
        {"store": "Myntra", "price": "₹51,000", "link": "https://myntra.com/example"},
    ]
