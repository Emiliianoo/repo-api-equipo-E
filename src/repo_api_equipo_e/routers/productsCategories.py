from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

@router.get("/api/productCategories")
def get_product_categories():
    uid, models, db, password = connect_odoo()

    categories = models.execute_kw(
        db, uid, password,
        "product.category", "search_read",
        [[]],
        {"fields": ["id", "name", "display_name"]}
    )

    return categories
    