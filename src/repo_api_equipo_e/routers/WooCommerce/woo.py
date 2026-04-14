from fastapi import APIRouter
from . import syncProducts

router = APIRouter(prefix="/woo", tags=["WooCommerce"])

router.include_router(syncProducts.router)