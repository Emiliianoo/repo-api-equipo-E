from fastapi import APIRouter

from repo_api_equipo_e.routers.Prestashop import updateProduct
from . import productSku, orderReference, customers, suppliers, payments, orders, products

router = APIRouter(prefix="/prestashop", tags=["PrestaShop"])

router.include_router(productSku.router)
router.include_router(orderReference.router)
router.include_router(customers.router)
router.include_router(suppliers.router)
router.include_router(payments.router)
router.include_router(products.router)
router.include_router(orders.router)
router.include_router(updateProduct.router)
