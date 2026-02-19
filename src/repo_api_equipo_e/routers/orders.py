from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

@router.get("/api/orders")
def get_orders():
    uid, models, db, password = connect_odoo()

    orders = models.execute_kw(
        db, uid, password,
        "sale.order", "search_read",
        [[]],
        {
            "fields": [
                "id",
                "name",
                "date_order",
                "state",
                "amount_total",
                "partner_id"
            ]
        }
    )
    return orders
