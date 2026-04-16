from fastapi import APIRouter, HTTPException
from ...models.woo import RequestedOrder
from repo_api_equipo_e.services.woo import create_woo_order
from starlette import status

router = APIRouter()

@router.post("/order", status_code=status.HTTP_201_CREATED)
def create_order(order: RequestedOrder):
    try:
        return create_woo_order(order)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
