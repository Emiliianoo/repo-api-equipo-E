from fastapi import APIRouter
from . import productSku, orderReference, order, product

router = APIRouter(prefix="/prestashop", tags=["PrestaShop"])

router.include_router(productSku.router)
router.include_router(orderReference.router)
router.include_router(order.router)
router.include_router(product.router)