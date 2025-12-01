from fastapi import APIRouter
from backend.services import price_service

router = APIRouter(prefix="/price", tags=["Price"])

@router.get("/")
async def get_prices(product: str):
    results = await price_service.get_all_prices(product)
    return {"product": product, "prices": results}
