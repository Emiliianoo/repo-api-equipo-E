from fastapi import APIRouter
from . import syncProducts, createProduct, createOrder, obtainOrders, getProducts

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)
router.include_router(createProduct.router)
router.include_router(createOrder.router)
router.include_router(obtainOrders.router)
router.include_router(getProducts.router)
