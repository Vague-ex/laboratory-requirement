from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .database import get_database
from .crud import get_all_items, insert_item
from .models import Item
import audit

app = FastAPI()

# CORS so frontend JS can call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to MongoDB
DB = get_database("mongodb+srv://Aguilar:Aguilar1@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority", "inventoryaudit")
COLLECTION = DB["inventoryitems"]

@app.get("/items")
def list_items():
    return get_all_items(COLLECTION)

@app.post("/items")
def add_item(item: Item):
    return insert_item(COLLECTION, item)

@app.get("/audit/cost_increase")
def audit_cost_increase(min_cost: float = Query(0), pct_increase: float = Query(10)):
    return audit.items_cost_increase(COLLECTION, min_cost, pct_increase, "2022", "2023")

@app.get("/audit/obsolete")
def audit_obsolete(threshold_qty: int = Query(100), cutoff_date: str = Query("2023-01-01")):
    return audit.obsolete_inventory(COLLECTION, threshold_qty, cutoff_date)
