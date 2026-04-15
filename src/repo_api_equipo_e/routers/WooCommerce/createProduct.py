from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from repo_api_equipo_e.services.woo import create_woo_product

router = APIRouter()

class ProductCreate(BaseModel):
  name: str
  description: Optional[str] = None
  price: float
  sku: Optional[str] = None
  stock_quantity: Optional[int] = None

@router.post("/products")
def create_product(product: ProductCreate):
    try:
        payload = {
            "name": product.name,
            "type": "simple",
            "regular_price": str(product.price),
            "sku": product.sku,
            "description": product.description or "",
            "manage_stock": product.stock_quantity is not None,
        }

        if product.stock_quantity is not None:
            payload["stock_quantity"] = product.stock_quantity

        result = create_woo_product(payload)

        return {
            "message": "Producto creado correctamente",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
