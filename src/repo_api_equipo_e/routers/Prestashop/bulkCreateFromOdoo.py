import os
import re
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

# ---------- XML helpers ----------
def _tag(xml: str, name: str):
    m = re.search(rf"<{name}[^>]*>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</{name}>", xml, re.S)
    return m.group(1).strip() if m else None

def _first_id(xml: str):
    # primer <id> encontrado en el xml
    return _tag(xml, "id")

# ---------- PRESTASHOP (usar XML para evitar respuestas raras JSON) ----------
async def get_product_id_by_reference(client, sku):
    r = await client.get(
        f"{BASE_URL}/api/products",
        params={"ws_key": API_KEY, "filter[reference]": f"[{sku}]", "display": "[id]"},
        headers={"Accept": "application/xml"},
    )
    return _first_id(r.text) if r.status_code == 200 else None

async def create_product(client, name, sku, price):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop><product>
<id_shop_default><![CDATA[1]]></id_shop_default>

<id_category_default><![CDATA[2]]></id_category_default>
<associations>
  <categories>
    <category><id><![CDATA[2]]></id></category>
  </categories>
</associations>

<reference><![CDATA[{sku}]]></reference>
<price><![CDATA[{price}]]></price>

<active><![CDATA[1]]></active>
<visibility><![CDATA[both]]></visibility>
<available_for_order><![CDATA[1]]></available_for_order>
<show_price><![CDATA[1]]></show_price>
<indexed><![CDATA[1]]></indexed>
<state><![CDATA[1]]></state>

<name><language id="1"><![CDATA[{name}]]></language></name>
<link_rewrite><language id="1"><![CDATA[{sku.lower()}]]></language></link_rewrite>
</product></prestashop>"""

    return await client.post(
        f"{BASE_URL}/api/products",
        params={"ws_key": API_KEY},
        headers={"Content-Type": "application/xml", "Accept": "application/xml"},
        content=xml.encode("utf-8"),
    )

async def get_stock_available_full_by_product(client, product_id):
    r = await client.get(
        f"{BASE_URL}/api/stock_availables",
        params={"ws_key": API_KEY, "filter[id_product]": f"[{product_id}]", "display": "full"},
        headers={"Accept": "application/xml"},
    )
    if r.status_code != 200:
        return None
    return r.text

def parse_stock_info(stock_xml: str):
    # toma el primer stock_available que venga
    return {
        "id": _tag(stock_xml, "id"),
        "id_product": _tag(stock_xml, "id_product"),
        "id_product_attribute": _tag(stock_xml, "id_product_attribute") or "0",
        "id_shop": _tag(stock_xml, "id_shop") or "1",
        "id_shop_group": _tag(stock_xml, "id_shop_group") or "0",  # 👈 en tu doc es 0
        "depends_on_stock": _tag(stock_xml, "depends_on_stock") or "0",
        "out_of_stock": _tag(stock_xml, "out_of_stock") or "2",
    }

async def patch_stock_quantity(client, stock_id, qty):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop><stock_available>
<id><![CDATA[{stock_id}]]></id>
<quantity><![CDATA[{int(qty)}]]></quantity>
</stock_available></prestashop>"""
    return await client.patch(
        f"{BASE_URL}/api/stock_availables/{stock_id}",
        params={"ws_key": API_KEY},
        headers={"Content-Type": "application/xml", "Accept": "application/xml"},
        content=xml.encode("utf-8"),
    )

async def put_stock_full(client, info, qty):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop><stock_available>
<id><![CDATA[{info['id']}]]></id>
<id_product><![CDATA[{info['id_product']}]]></id_product>
<id_product_attribute><![CDATA[{info['id_product_attribute']}]]></id_product_attribute>
<id_shop><![CDATA[{info['id_shop']}]]></id_shop>
<id_shop_group><![CDATA[{info['id_shop_group']}]]></id_shop_group>
<quantity><![CDATA[{int(qty)}]]></quantity>
<depends_on_stock><![CDATA[{info['depends_on_stock']}]]></depends_on_stock>
<out_of_stock><![CDATA[{info['out_of_stock']}]]></out_of_stock>
</stock_available></prestashop>"""
    return await client.put(
        f"{BASE_URL}/api/stock_availables/{info['id']}",
        params={"ws_key": API_KEY},
        headers={"Content-Type": "application/xml", "Accept": "application/xml"},
        content=xml.encode("utf-8"),
    )

# ---------- ENDPOINT PRINCIPAL ----------
@router.get("/products/from-odoo/bulk")
async def import_products_from_odoo():

    if not BASE_URL or not API_KEY:
        return {"status":"error","data":None,"errors":[{"code":"500","message":"PrestaShop no configurado"}]}

    created, updated, skipped_price_stock_0, create_errors, stock_errors = [], [], [], [], []
    products = get_odoo_products()

    async with httpx.AsyncClient(timeout=40) as client:
        for p in products:
            sku = (p.get("default_code") or "").strip()
            name = (p.get("name") or "").strip()
            price = float(p.get("list_price") or 0)
            stock = float(p.get("qty_available") or 0)

            if not sku:
                create_errors.append(p.get("id"))
                continue

            # NO crear si precio=0 Y stock=0
            if price == 0 and stock == 0:
                skipped_price_stock_0.append(sku)
                continue

            # buscar por reference
            product_id = await get_product_id_by_reference(client, sku)

            # Si no existe, crear
            if not product_id:
                rc = await create_product(client, name, sku, price)
                if rc.status_code not in (200, 201):
                    create_errors.append(sku)
                    continue
                product_id = await get_product_id_by_reference(client, sku)
                if not product_id:
                    create_errors.append(sku)
                    continue
                created.append(sku)
            else:
                updated.append(sku)

            # Stock: GET stock_available (se crea automáticamente)
            stock_xml = await get_stock_available_full_by_product(client, product_id)
            if not stock_xml:
                stock_errors.append(sku)
                continue

            info = parse_stock_info(stock_xml)
            if not info["id"]:
                stock_errors.append(sku)
                continue

            # PATCH quantity. Si falla, fallback a PUT completo.
            rs = await patch_stock_quantity(client, info["id"], stock)
            if rs.status_code not in (200, 201):
                rs2 = await put_stock_full(client, info, stock)
                if rs2.status_code not in (200, 201):
                    stock_errors.append(sku)

    return {
        "status":"success",
        "data":{
            "created": created,
            "updated_existing": updated,
            "skipped_price0_stock0": skipped_price_stock_0,
            "create_errors": create_errors,
            "stock_errors": stock_errors
        },
        "errors":[]
    }