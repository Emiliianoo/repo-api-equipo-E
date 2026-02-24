from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

@router.get("/productStock")
def get_product_stock():
    uid, models, db, password = connect_odoo()

    stock_quant = models.execute_kw(
        db, uid, password,
        "stock.quant", "search_read",
        [[]],
        {"fields": ["id", "product_id", "location_id", "quantity"]}
    )
    return stock_quant
