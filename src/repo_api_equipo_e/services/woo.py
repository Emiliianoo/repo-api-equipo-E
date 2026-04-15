from woocommerce import API
import os

wcapi = API(
    url=os.getenv("WC_URL"),
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3",
    timeout=20
)

def create_woo_product(payload: dict):
    response = wcapi.post("products", payload)

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Error al crear producto en WooCommerce: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()