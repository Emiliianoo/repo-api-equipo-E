import os
import httpx
import xml.etree.ElementTree as ET
from fastapi import APIRouter

router = APIRouter()

BASE_URL = os.getenv("PRESTASHOP_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("PRESTASHOP_API_KEY", "")


async def _get_product_by_reference(client: httpx.AsyncClient, reference: str):
    response = await client.get(
        f"{BASE_URL}/api/products",
        params={
            "ws_key": API_KEY,
            "filter[reference]": f"[{reference}]",
            "display": "full",
            "output_format": "JSON",
            "limit": 1
        }
    )
    return response


async def _get_product_xml_by_id(client: httpx.AsyncClient, product_id: str):
    response = await client.get(
        f"{BASE_URL}/api/products/{product_id}",
        params={"ws_key": API_KEY},
        headers={"Accept": "application/xml"}
    )
    return response


async def _disable_product_active_field(client: httpx.AsyncClient, product_id: str):
    product_xml_response = await _get_product_xml_by_id(client, product_id)

    if product_xml_response.status_code != 200:
        return product_xml_response

    try:
        root = ET.fromstring(product_xml_response.text)
    except ET.ParseError:
        return product_xml_response

    active_node = root.find(".//product/active")
    if active_node is None:
        return product_xml_response

    active_node.text = "0"

    product_node = root.find(".//product")
    if product_node is not None:
        non_writable_fields = {
            "manufacturer_name",
            "quantity",
            "position_in_category",
            "id_default_image",
            "id_default_combination",
        }
        for child in list(product_node):
            tag_name = child.tag.split("}")[-1]
            if tag_name in non_writable_fields:
                product_node.remove(child)

    xml_payload = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    response = await client.put(
        f"{BASE_URL}/api/products/{product_id}",
        params={"ws_key": API_KEY},
        headers={"Content-Type": "application/xml"},
        content=xml_payload
    )
    return response


@router.get("/product/{reference}")
async def deactivate_product(reference: str):

    if not BASE_URL or not API_KEY:
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": "500",
                    "message": "PrestaShop no configurado"
                }
            ]
        }

    async with httpx.AsyncClient() as client:
        product_response = await _get_product_by_reference(client, reference)

        if product_response.status_code != 200:
            return {
                "status": "error",
                "data": None,
                "errors": [
                    {
                        "code": str(product_response.status_code),
                        "message": "Error al consultar PrestaShop"
                    }
                ]
            }

        product_data = product_response.json()
        products = product_data if isinstance(product_data, list) else product_data.get("products", [])

        if not products:
            return {
                "status": "error",
                "data": None,
                "errors": [
                    {
                        "code": "404",
                        "message": "Producto no encontrado"
                    }
                ]
            }

        product = products[0]
        product_id = str(product.get("id", "")).strip()

        if not product_id:
            return {
                "status": "error",
                "data": None,
                "errors": [
                    {
                        "code": "500",
                        "message": "El producto no tiene id válido"
                    }
                ]
            }

        update_response = await _disable_product_active_field(client, product_id)

    if update_response.status_code not in (200, 201):
        error_detail = update_response.text[:300] if update_response.text else ""
        return {
            "status": "error",
            "data": None,
            "errors": [
                {
                    "code": str(update_response.status_code),
                    "message": "No se pudo desactivar el producto en PrestaShop",
                    "detail": error_detail
                }
            ]
        }

    composed_name = product.get("name", "")
    name = composed_name[0].get("value") if isinstance(composed_name, list) else composed_name

    return {
        "status": "success",
        "data": {
            "id": product.get("id"),
            "nombre": name,
            "referencia": product.get("reference"),
            "precio": product.get("price"),
            "stock": product.get("quantity"),
            "activo": "No"
        },
        "errors": []
    }
