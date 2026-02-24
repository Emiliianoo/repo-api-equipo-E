from fastapi import APIRouter
from .Odoo.odoo import router as odoo_router
from .Prestashop.prestashop import router as prestashop_router

router = APIRouter(prefix="/api")

router.include_router(odoo_router)
router.include_router(prestashop_router)