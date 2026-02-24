from fastapi import APIRouter
from . import productSku, orderReference, customers, suppliers, payments, orders, products

router = APIRouter(prefix="/prestashop", tags=["PrestaShop"])

router.include_router(productSku.router)
router.include_router(orderReference.router)
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(payments.router)
router.include_router(products.router)
router.include_router(orders.router)
