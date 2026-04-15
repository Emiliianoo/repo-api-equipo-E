from fastapi import APIRouter
from . import syncProducts, createProduct

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)
router.include_router(createProduct.router)