from fastapi import APIRouter, HTTPException
from repo_api_equipo_e.services.odoo import fetch_odoo_products
from woocommerce import API
import os
from dotenv import load_dotenv
from repo_api_equipo_e.services.woo import create_woo_product

load_dotenv()

router = APIRouter()

wcapi = API(
    url=os.getenv("WC_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=20
)


def get_woo_product_by_sku(sku: str):
    response = wcapi.get("products", params={"sku": sku})

    if response.status_code != 200:
        raise Exception(
            f"Error al buscar producto en WooCommerce: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()


@router.post("/sync-products")
def sync_products_to_woo():
    try:
        odoo_products = fetch_odoo_products()

        created = []
        skipped = []
        failed = []

        for product in odoo_products:
            sku = product.get("default_code") or f"odoo-{product['id']}"

            existing = get_woo_product_by_sku(sku)
            if existing:
                skipped.append({
                    "odoo_id": product["id"],
                    "name": product["name"],
                    "sku": sku,
                    "reason": "Ya existe en WooCommerce"
                })
                continue

            payload = {
                "name": product["name"],
                "type": "simple",
                "regular_price": str(product.get("list_price", 0) or 0),
                "sku": sku,
                "description": f"Producto importado desde Odoo. ID Odoo: {product['id']}",
                "short_description": product["name"],
                "manage_stock": False
            }

            try:
                new_product = create_woo_product(payload)
                created.append(new_product)
            except Exception as e:
                failed.append({
                    "odoo_id": product["id"],
                    "name": product["name"],
                    "sku": sku,
                    "error": str(e)
                })

        return {
            "message": "Sincronización completada",
            "total_odoo": len(odoo_products),
            "created_count": len(created),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "created": created,
            "skipped": skipped,
            "failed": failed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))