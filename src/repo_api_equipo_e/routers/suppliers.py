from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

@router.get("/api/suppliers")
def get_suppliers():
    uid, models, db, password = connect_odoo()

    suppliers = models.execute_kw(
        db, uid, password,
        "res.partner", "search_read",
        [[("supplier_rank", ">", 0)]],
        {"fields": ["id", "name", "active", "contact_address", "email", "is_company", "display_name"]}
    )
    return suppliers
