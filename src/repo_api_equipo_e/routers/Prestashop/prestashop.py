from fastapi import APIRouter
from . import productSku

router = APIRouter(prefix="/prestashop", tags=["PrestaShop"])

router.include_router(productSku.router)