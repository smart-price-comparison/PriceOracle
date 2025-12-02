# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from backend.routes import price_routes

app = FastAPI(
    title="PriceOracle API",
    version="1.0",
)

# ---------------------------
# CORS — allows frontend to access backend API
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # allow all origins for now (safe for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Include Routes
# ---------------------------
app.include_router(price_routes.router)


# ---------------------------
# Root endpoint
# ---------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to PriceOracle API!"}


# ---------------------------
# Startup Event (NO DB INIT)
# ---------------------------
@app.on_event("startup")
async def startup_event():
    # No database initialization for now (prevents crashes)
    pass
