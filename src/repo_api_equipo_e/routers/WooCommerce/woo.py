from fastapi import APIRouter
from . import syncProducts, createProduct, createOrder, obtainOrders

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)
router.include_router(createProduct.router)
router.include_router(createOrder.router)
router.include_router(obtainOrders.router)