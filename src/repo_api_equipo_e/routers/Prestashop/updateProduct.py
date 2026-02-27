import os
import httpx
from fastapi import APIRouter


router = APIRouter()

ODDO_URL = os.getenv("ODOO_URL", "").rstrip("/")
BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@router.get("/update-products")
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
        r = await client.get(
            f"{BASE_URL}/api/products",
            params={
                "ws_key": API_KEY,
                "display": "full",
                "output_format": "JSON"
            }
        )

    # if r.status_code != 200:
    #     return {
    #         "status": "error",
    #         "data": None,
    #         "errors": [
    #             {
    #                 "code": str(r.status_code),
    #                 "message": "Error al consultar PrestaShop"
    #             }
    #         ]
    #     }
    
    data = r.json()

    if isinstance(data, dict):
        products = data.get("products", [])
    else:
        products = data

    if not products:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "404",
                    "message": "Productos no encontrados"
                }
            ]
        }
    
    updatedProducts = []

    for product in products:
        composed_name = product.get("name", "")
        name = composed_name[0].get("value") if isinstance(composed_name, list) else composed_name
        
        updatedProducts.append({
            "id": product.get("id"),
            "nombre": name,
            "referencia": product.get("reference"),
            "precio": product.get("price"),
            "stock": product.get("quantity"),
            "activo": "Sí" if product.get("active") == "1" else "No"
        })

    async with httpx.AsyncClient() as client:
        response = await client.put(f"{ODDO_URL}/products", json=updatedProducts)

    # SUCCESS
    return {
        "status": "success",
        "data": updatedProducts,
        "errors": []
    }
