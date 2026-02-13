import os
import xmlrpc.client

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

def connect_odoo():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise HTTPException(status_code=401, detail="Error al conectar con Odoo")

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

@app.get("/api/products")
def get_products():
    uid, models = connect_odoo()

    products = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "product.product", "search_read",
        [[]],
        {"fields": ["id", "name", "default_code", "list_price"]}
    )

    return products

@app.get("/api/suppliers")
def get_providers():
    uid, models = connect_odoo()

    suppliers = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "res.partner", "search_read",
        [[("supplier_rank", ">", 0)]],
        {"fields": ["id", "name", "active", "contact_address", "email", "is_company", "display_name"]}
    )
    return suppliers