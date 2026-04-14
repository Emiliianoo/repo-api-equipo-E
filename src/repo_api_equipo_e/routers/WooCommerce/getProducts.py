from urllib import response

from fastapi import APIRouter, HTTPException
from repo_api_equipo_e.services.odoo import fetch_odoo_products
from woocommerce import API
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

wcapi = API(
    url=os.getenv("WC_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=20
)

    
@router.get("/products")
def get_woo_product_by_sku():
    response = wcapi.get("products")

    if response.status_code != 200:
        raise Exception(
            f"Error al buscar producto en WooCommerce: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()