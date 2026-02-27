import os
import httpx
from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")

# ---------- ODOO ----------
def get_odoo_products():
    uid, models, db, password = connect_odoo()
    return models.execute_kw(
        db, uid, password,
        "product.product", "search_read",
        [[]],
        {"fields": ["id", "name", "default_code", "list_price", "qty_available"]}
    )

# ---------- PRESTASHOP ----------
async def product_exists(client, sku):
    r = await client.get(
        f"{BASE_URL}/api/products",
        params={
            "ws_key": API_KEY,
            "filter[reference]": f"[{sku}]",
            "output_format": "JSON",
            "limit": 1
        }
    )
    data = r.json()
    products = data if isinstance(data, list) else data.get("products", [])
    return bool(products)

async def create_product(client, name, sku, price):
    xml = f"""<?xml version="1.0"?>
<prestashop><product>
<name><language id="1">{name}</language></name>
<reference>{sku}</reference>
<price>{price}</price>
<active>1</active>
<available_for_order>1</available_for_order>
<state>1</state>
</product></prestashop>"""
    return await client.post(
        f"{BASE_URL}/api/products",
        params={"ws_key": API_KEY},
        headers={"Content-Type": "application/xml"},
        content=xml.encode()
    )

# ---------- ENDPOINT ----------
@router.post("/products/from-odoo/bulk")
async def create_products_bulk():

    if not BASE_URL or not API_KEY:
        return {"status": "error", "data": None, "errors": [{"code":"500","message":"PrestaShop no configurado"}]}

    created, skipped_no_stock, skipped_exists, failed = [], [], [], []

    products = get_odoo_products()

    async with httpx.AsyncClient(timeout=20) as client:
        for p in products:
            sku = (p.get("default_code") or "").strip()
            stock = p.get("qty_available") or 0

            if not sku or stock <= 0:
                skipped_no_stock.append(p.get("id"))
                continue

            if await product_exists(client, sku):
                skipped_exists.append(sku)
                continue

            r = await create_product(client, p.get("name",""), sku, p.get("list_price") or 0)
            (created if r.status_code in (200, 201) else failed).append(sku)

    return {
        "status": "success",
        "data": {
            "created": created,
            "skipped_no_stock": skipped_no_stock,
            "skipped_exists": skipped_exists,
            "errors": failed
        },
        "errors": []
    }