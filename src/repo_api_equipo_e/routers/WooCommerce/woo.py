from fastapi import APIRouter
from . import syncProducts, createProduct, createOrder

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)
router.include_router(createProduct.router)
router.include_router(createOrder.router)