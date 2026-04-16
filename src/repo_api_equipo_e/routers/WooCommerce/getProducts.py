
from urllib import response

from fastapi import APIRouter, HTTPException
from requests import models
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
def get_woo_products():
    
    response = wcapi.get("products", params={"per_page": 10})

    if response.status_code == 200:
        productos = response.json()
        print(f"--- Se encontraron {len(productos)} productos ---")

        for p in productos:
            print(f"ID: {p['id']} | Nombre: {p['name']} | Precio: ${p['price']}")
    else:
        print(f"Error {response.status_code}: {response.text}")


    return response.json()