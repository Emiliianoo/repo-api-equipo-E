from fastapi import APIRouter
from . import orders, products, suppliers, stock, productsCategories

router = APIRouter(prefix="/odoo")

router.include_router(orders.router)
router.include_router(products.router)
router.include_router(suppliers.router)
router.include_router(stock.router)
router.include_router(productsCategories.router)