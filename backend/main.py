from fastapi import FastAPI
from backend.routes import price_routes

app = FastAPI(title="PriceOracle API", version="1.0")

# Include your router
app.include_router(price_routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to PriceOracle API!"}
