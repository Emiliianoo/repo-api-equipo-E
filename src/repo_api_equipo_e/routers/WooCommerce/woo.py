from fastapi import APIRouter
from . import syncProducts
from . import getProducts

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)
router.include_router(getProducts.router)