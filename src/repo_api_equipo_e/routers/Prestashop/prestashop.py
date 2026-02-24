from fastapi import APIRouter
from . import productSku, orderReference, customers, suppliers, payments

router = APIRouter(prefix="/prestashop", tags=["PrestaShop"])

router.include_router(productSku.router)
router.include_router(orderReference.router)
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(payments.router)
