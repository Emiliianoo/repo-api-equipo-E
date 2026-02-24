import os
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")

@router.get("/order/{reference}")
async def get_order_by_reference(reference: str):

    if not BASE_URL or not API_KEY:
        raise HTTPException(500, "PrestaShop no configurado")

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/api/orders",
            params={
                "ws_key": API_KEY,
                "filter[reference]": f"[{reference}]",
                "display": "full",
                "output_format": "JSON"
            }
        )

    if r.status_code != 200:
        raise HTTPException(502, "Error en PrestaShop")

    data = r.json()

    orders = data.get("orders", [])
    if not orders:
        raise HTTPException(404, "Orden no encontrada")

    return orders[0]