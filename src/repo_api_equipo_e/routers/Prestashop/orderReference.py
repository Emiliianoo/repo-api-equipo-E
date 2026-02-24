import os
import httpx
from fastapi import APIRouter

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@router.get("/order/{reference}")
async def get_order_by_reference(reference: str):

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
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": str(r.status_code),
                    "message": "Error al consultar PrestaShop"
                }
            ]
        }
    
    data = r.json()

    if isinstance(data, list):
        orders = data
    else:
        orders = data.get("orders", [])

    if not orders:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "404",
                    "message": "Orden no encontrada"
                }
            ]
        }

    return {
        "status": "success",
        "data": orders[0],
        "errors": []
    }