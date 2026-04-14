from fastapi import APIRouter
from .Odoo.odoo import router as odoo_router
from .Prestashop.prestashop import router as prestashop_router
from .WooCommerce.woo import router as woo_router

router = APIRouter(prefix="/api")

router.include_router(odoo_router)
router.include_router(prestashop_router)
router.include_router(woo_router)