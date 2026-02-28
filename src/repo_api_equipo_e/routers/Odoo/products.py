from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

@router.get("/products")
def get_products():
    uid, models, db, password = connect_odoo()
    
    products = models.execute_kw(
        db, uid, password,
        "product.product", "search_read",
        [[]],
        {"fields": ["id", "name", "default_code", "list_price"]}
    )
    return products
