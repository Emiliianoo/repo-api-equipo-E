import os
import httpx
from fastapi import APIRouter

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@router.get("/product/{sku}")
async def get_product_by_sku(sku: str):

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
            f"{BASE_URL}/api/products",
            params={
                "ws_key": API_KEY,
                "filter[reference]": f"[{sku}]",
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
        products = data
    else:
        products = data.get("products", [])

    if not products:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "404",
                    "message": "Producto no encontrado"
                }
            ]
        }

    # SUCCESS
    return {
        "status": "success",
        "data": products[0],
        "errors": []
    }