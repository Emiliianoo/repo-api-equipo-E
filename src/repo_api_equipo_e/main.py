from fastapi import FastAPI
from repo_api_equipo_e.routers import products, suppliers, stock, productsCategories

app = FastAPI()

app.include_router(products.router)
app.include_router(suppliers.router)
app.include_router(stock.router)
app.include_router(productsCategories.router)
