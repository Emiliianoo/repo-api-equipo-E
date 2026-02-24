import os
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@router.get("/product/{sku}")
async def get_product_by_sku(sku: str):

    if not BASE_URL or not API_KEY:
        raise HTTPException(500, "PrestaShop no configurado")

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/api/products",
            params={
                "ws_key": API_KEY,
                "filter[reference]": f"[{sku}]",
                "display": "full",
                "output_format": "JSON"
            }
        )

    if r.status_code != 200:
        raise HTTPException(502, "Error en PrestaShop")

    data = r.json()

    products = data.get("products", [])
    if not products:
        raise HTTPException(404, "Producto no encontrado")

    return products[0]
