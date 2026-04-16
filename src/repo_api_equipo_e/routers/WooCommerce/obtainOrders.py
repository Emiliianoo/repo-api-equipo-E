from fastapi import APIRouter
from repo_api_equipo_e.services.woo import get_woo_orders

router = APIRouter()

@router.get("/orders")
def obtain_orders():
    return get_woo_orders()