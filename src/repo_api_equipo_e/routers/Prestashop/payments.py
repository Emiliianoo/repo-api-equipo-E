import os
import httpx
from fastapi import APIRouter

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


@router.get("/payments")
async def get_payments():
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
            f"{BASE_URL}/api/order_payments",
            params={
                "ws_key": API_KEY,
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
                    "message": "Error al consultar pagos en PrestaShop"
                }
            ]
        }

    data = r.json()
    return {
        "status": "success",
        "data": data,
        "errors": []
    }


@router.get("/payments/{payment_id}")
async def get_payment(payment_id: int):
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
            f"{BASE_URL}/api/order_payments/{payment_id}",
            params={
                "ws_key": API_KEY,
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
                    "message": "Error al obtener pago en PrestaShop"
                }
            ]
        }

    data = r.json()
    return {
        "status": "success",
        "data": data,
        "errors": []
    }