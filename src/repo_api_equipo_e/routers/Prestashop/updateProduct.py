import os
import re
import httpx
import xml.etree.ElementTree as ET
from fastapi import APIRouter
from repo_api_equipo_e.odoo import connect_odoo

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")

# ---------- ODOO ----------
def get_odoo_products(reference):
    uid, models, db, password = connect_odoo()
    return models.execute_kw(
        db, uid, password,
        "product.product", "search_read",
        [[("default_code", "=", reference)]],
        {"fields": ["id", "name", "default_code", "list_price", "qty_available"]}
    )

def get_all_odoo_products():
    uid, models, db, password = connect_odoo()
    return models.execute_kw(
        db, uid, password,
        "product.product", "search_read",
        [[]],
        {"fields": ["id", "name", "default_code", "list_price", "qty_available"]}
    )

def update_odoo_product(product_id, data):
    uid, models, db, password = connect_odoo()
    return models.execute_kw(
        db, uid, password,
        "product.product", "write",
        [[product_id], data]
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

async def get_all_prestashop_products(client):
    """Obtiene todos los productos de PrestaShop con referencia"""
    r = await client.get(
        f"{BASE_URL}/api/products",
        params={"ws_key": API_KEY, "display": "full"},
        headers={"Accept": "application/xml"},
    )
    if r.status_code != 200:
        return []
    
    products = []
    # Buscar todos los <product> en el XML
    try:
        root = ET.fromstring(r.text)
        for product_elem in root.findall("product"):
            product_id = product_elem.findtext("id")
            reference = product_elem.findtext("reference")
            price = product_elem.findtext("price")
            name = product_elem.findtext("name/language")
            
            if product_id and reference:
                products.append({
                    "id": product_id,
                    "reference": reference,
                    "price": float(price or 0),
                    "name": name or "",
                })
    except Exception as e:
        print(f"Error parsing Prestashop products: {e}")
    
    return products

async def get_prestashop_stock(client, product_id):
    """Obtiene el stock de un producto en PrestaShop"""
    r = await client.get(
        f"{BASE_URL}/api/stock_availables",
        params={"ws_key": API_KEY, "filter[id_product]": f"[{product_id}]", "display": "full"},
        headers={"Accept": "application/xml"},
    )
    if r.status_code != 200:
        return 0
    
    stock_qty = _tag(r.text, "quantity")
    return float(stock_qty or 0)

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
        "id_shop_group": _tag(stock_xml, "id_shop_group") or "0",
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
@router.get("/products/from-odoo/{reference}")
async def import_product_from_odoo(reference):
    if not BASE_URL or not API_KEY:
        return {"status":"error","data":None,"errors":[{"code":"500","message":"PrestaShop no configurado"}]}

    results = get_odoo_products(reference)
    if not results:
        return {"status": "error", "message": "Referencia no encontrada en Odoo"}
    product = results[0]

    async with httpx.AsyncClient(timeout=40) as client:
        sku = (product.get("default_code") or "").strip()
        name = (product.get("name") or "").strip()
        price = float(product.get("list_price") or 0)
        stock = float(product.get("qty_available") or 0)

        # NO crear si precio=0 Y stock=0
        if price == 0 and stock == 0:
            return {"status": "skipped",
                    "message": "Precio y stock en cero"}

        # buscar por reference
        product_id = await get_product_id_by_reference(client, sku)
        action_taken = "actualizado" if product_id else "creado"

        # Si no existe, crear
        if not product_id:
            rc = await create_product(client, name, sku, price)
            if rc.status_code not in (200, 201):
                return {"status": "error", "message": "Error al crear el producto en PrestaShop"}
            product_id = await get_product_id_by_reference(client, sku)
            if not product_id:
                return {"status": "error", "message": "Producto creado pero no se pudo recuperar el ID"}

        # Stock: GET stock_available (se crea automáticamente)
        stock_xml = await get_stock_available_full_by_product(client, product_id)
        if not stock_xml:
            return {"status": "skipped",
                    "message": "No se encontró el registro de inventario"}

        info = parse_stock_info(stock_xml)
        if not info["id"]:
            return {"status": "skipped",
                    "message": "ID de inventario no válido"}

        # PATCH quantity. Si falla, fallback a PUT completo.
        rs = await patch_stock_quantity(client, info["id"], stock)
        if rs.status_code not in (200, 201):
            rs2 = await put_stock_full(client, info, stock)
            if rs2.status_code not in (200, 201):
                return {"status": "error", "message": "No se pudo actualizar la cantidad de stock"}
        
        return {
            "status": "success",
            "message": f"Producto {action_taken} correctamente",
            "data": {
                "id_prestashop": product_id,
                "referencia": sku,
                "nombre": name,
                "precio": price,
                "stock_sincronizado": stock
            }
        }

# ---------- SINCRONIZACIÓN PRESTASHOP -> ODOO ----------
@router.get("/sync/prestashop-to-odoo")
async def sync_prestashop_to_odoo():
    """
    Verifica cambios en PrestaShop y los actualiza en Odoo
    Compara precios y cantidades
    """
    if not BASE_URL or not API_KEY:
        return {"status": "error", "data": None, "errors": [{"code": "500", "message": "PrestaShop no configurado"}]}
    
    try:
        # Obtener productos de Odoo
        odoo_products = get_all_odoo_products()
        odoo_by_ref = {p.get("default_code"): p for p in odoo_products if p.get("default_code")}
        
        # Obtener productos de PrestaShop
        async with httpx.AsyncClient(timeout=40) as client:
            prestashop_products = await get_all_prestashop_products(client)
            
            updates_made = []
            errors = []
            
            for ps_product in prestashop_products:
                reference = ps_product["reference"]
                
                # Buscar producto en Odoo por referencia
                if reference not in odoo_by_ref:
                    continue
                
                odoo_product = odoo_by_ref[reference]
                odoo_id = odoo_product["id"]
                
                # Obtener stock en PrestaShop
                ps_stock = await get_prestashop_stock(client, ps_product["id"])
                
                changes = {}
                
                # Comparar precio
                if ps_product["price"] != odoo_product.get("list_price", 0):
                    changes["list_price"] = ps_product["price"]
                
                # Comparar stock
                if ps_stock != odoo_product.get("qty_available", 0):
                    changes["qty_available"] = ps_stock
                
                # Si hay cambios, actualizar Odoo
                if changes:
                    try:
                        update_odoo_product(odoo_id, changes)
                        updates_made.append({
                            "reference": reference,
                            "odoo_id": odoo_id,
                            "changes": changes
                        })
                    except Exception as e:
                        errors.append({
                            "reference": reference,
                            "error": str(e)
                        })
        
        return {
            "status": "success",
            "message": f"Sincronización completada",
            "data": {
                "updates_made": len(updates_made),
                "errors_count": len(errors),
                "updates": updates_made,
                "errors": errors
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en sincronización: {str(e)}",
            "data": None
        }

@router.get("/sync/prestashop-to-odoo/{reference}")
async def sync_prestashop_product_to_odoo(reference):
    """
    Sincroniza un producto específico de PrestaShop a Odoo
    """
    if not BASE_URL or not API_KEY:
        return {"status": "error", "data": None, "errors": [{"code": "500", "message": "PrestaShop no configurado"}]}
    
    try:
        # Obtener producto de Odoo
        odoo_products = get_odoo_products(reference)
        if not odoo_products:
            return {"status": "error", "message": f"Producto con referencia {reference} no encontrado en Odoo"}
        
        odoo_product = odoo_products[0]
        odoo_id = odoo_product["id"]
        
        async with httpx.AsyncClient(timeout=40) as client:
            # Obtener producto de PrestaShop
            product_id = await get_product_id_by_reference(client, reference)
            if not product_id:
                return {"status": "error", "message": f"Producto con referencia {reference} no encontrado en PrestaShop"}
            
            # Obtener detalles del producto PrestaShop
            ps_products = await get_all_prestashop_products(client)
            ps_product = next((p for p in ps_products if p["id"] == product_id), None)
            
            if not ps_product:
                return {"status": "error", "message": "No se pudieron obtener detalles del producto PrestaShop"}
            
            # Obtener stock
            ps_stock = await get_prestashop_stock(client, product_id)
            
            changes = {}
            
            # Comparar precio
            if ps_product["price"] != odoo_product.get("list_price", 0):
                changes["list_price"] = ps_product["price"]
            
            # Comparar stock
            if ps_stock != odoo_product.get("qty_available", 0):
                changes["qty_available"] = ps_stock
            
            if not changes:
                return {
                    "status": "skipped",
                    "message": "No hay cambios para sincronizar",
                    "data": {
                        "reference": reference,
                        "prestashop_price": ps_product["price"],
                        "odoo_price": odoo_product.get("list_price", 0),
                        "prestashop_stock": ps_stock,
                        "odoo_stock": odoo_product.get("qty_available", 0)
                    }
                }
            
            # Actualizar Odoo
            update_odoo_product(odoo_id, changes)
            
            return {
                "status": "success",
                "message": f"Producto {reference} sincronizado correctamente",
                "data": {
                    "reference": reference,
                    "odoo_id": odoo_id,
                    "changes": changes,
                    "previous_values": {
                        "list_price": odoo_product.get("list_price", 0),
                        "qty_available": odoo_product.get("qty_available", 0)
                    },
                    "new_values": {
                        "list_price": changes.get("list_price", odoo_product.get("list_price", 0)),
                        "qty_available": changes.get("qty_available", odoo_product.get("qty_available", 0))
                    }
                }
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en sincronización: {str(e)}",
            "data": None
        }

