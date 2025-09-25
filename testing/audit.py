from datetime import datetime
from pymongo.collection import Collection

def items_cost_increase(collection: Collection, min_cost: float, pct_increase: float, last_year: str, this_year: str):
    query = {
        "$expr": {
            "$and": [
                {"$gt": [f"${this_year}_unit_cost", min_cost]},
                {
                    "$gt": [
                        {"$divide": [{"$subtract": [f"${this_year}_unit_cost", f"${last_year}_unit_cost"]}, f"${last_year}_unit_cost"]},
                        pct_increase / 100
                    ]
                }
            ]
        }
    }
    return list(collection.find(query, {"_id": 0}))

def obsolete_inventory(collection: Collection, threshold_qty: int, cutoff_date: str):
    cutoff = datetime.fromisoformat(cutoff_date)
    query = {
        "quantity": {"$gt": threshold_qty},
        "last_sale_date": {"$lt": cutoff.isoformat()}
    }
    return list(collection.find(query, {"_id": 0}))
