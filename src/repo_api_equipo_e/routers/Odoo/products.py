from fastapi import APIRouter
from repo_api_equipo_e.services.odoo import fetch_odoo_products

router = APIRouter()

@router.get("/products")
def get_products():
    return fetch_odoo_products()
