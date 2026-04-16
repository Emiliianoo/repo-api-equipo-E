from woocommerce import API
import os
from ..models.woo import RequestedOrder

wcapi = None

def _get_wcapi():
    global wcapi
    if wcapi is None:
        wcapi = API(
            url=os.getenv("WORDPRESS_BASE_URL"),
            consumer_key=os.getenv("WOOCOMMERCE_CONSUMER_KEY"),
            consumer_secret=os.getenv("WOOCOMMERCE_CONSUMER_SECRET"),
            version="wc/v3",
            timeout=20
        )
    return wcapi

def create_woo_product(payload: dict):
    response = _get_wcapi().post("products", payload)

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Error al crear producto en WooCommerce: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()

def create_woo_order(order:RequestedOrder):
    payload = order.model_dump()
    response = _get_wcapi().post("orders", payload)

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Error al crear la orden en WooCommerce: "
            f"{response.status_code} - {response.text}"
        )
    return response.json()

def get_woo_orders():
    try:
        response = _get_wcapi().get("orders")
        
        if response.status_code != 200:
            return {"error": f"{response.status_code}", "message": response.text}
        
        return response.json()
    except Exception as e:
        return {"error": str(e)}