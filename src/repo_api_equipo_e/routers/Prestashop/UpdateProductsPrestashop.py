import os
import httpx
from fastapi import APIRouter


router = APIRouter()

ODDO_URL = os.getenv("ODOO_URL", "").rstrip("/")
BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@app.get("/update-products")
async def update_products_prestashop():

    if not BASE_URL or not API_KEY:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "500",
                    "message": "PrestaShop no configurado"
                }
            ]
        }

    async with httpx.AsyncClient() as client:
        r = await client.put(f"{ODDO_URL}/api/products",)

    