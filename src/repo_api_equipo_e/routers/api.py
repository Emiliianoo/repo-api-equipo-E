from fastapi import APIRouter
from .Odoo.odoo import router as odoo_router

router = APIRouter(prefix="/api")

router.include_router(odoo_router)