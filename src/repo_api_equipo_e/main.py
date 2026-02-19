from fastapi import FastAPI
from repo_api_equipo_e.routers import products, suppliers, stock, orders

app = FastAPI()

app.include_router(products.router)
app.include_router(suppliers.router)
app.include_router(stock.router)
app.include_router(orders.router)
