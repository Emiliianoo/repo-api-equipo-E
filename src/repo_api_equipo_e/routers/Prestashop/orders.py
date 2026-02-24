import os
import httpx
from fastapi import APIRouter

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")

@router.get("/orders")
async def getOrders():
  
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
                "display": "full",
                "output_format": "JSON"
            }
        )
        print(f"Status Code: {r.status_code}")
        print(f"Respuesta: {r.text}")

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

    if isinstance(data, dict):
        orders = data.get("orders", [])
    else:
        orders = data

    if not orders:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "404",
                    "message": "Ordenes no encontradas"
                }
            ]
        }
    cleaned_orders = []
    for order in orders:
        cleaned_orders.append({
            "id": order.get("id"),
            "referencia": order.get("reference"),
            "total_pagado": order.get("total_paid"),
            "fecha": order.get("date_add"),
            "id_cliente": order.get("id_customer"),
            "estado_actual": order.get("current_state")
        })

    return {
        "status": "success",
        "data": cleaned_orders,
        "errors": []
    }