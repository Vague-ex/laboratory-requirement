from datetime import datetime
from pymongo.collection import Collection

def cost_increase(collection: Collection, last_year: str, this_year: str, min_cost: float, pct_increase: float):
    pipeline = [
        {
            "$match": {
                f"{this_year}_unit_cost": {"$gt": min_cost},
                "$expr": {
                    "$gt": [
                        {
                            "$divide": [
                                {"$subtract": [f"${this_year}_unit_cost", f"${last_year}_unit_cost"]},
                                f"${last_year}_unit_cost"
                            ]
                        },
                        pct_increase / 100
                    ]
                }
            }
        }
    ]
    return list(collection.aggregate(pipeline))

def obsolete_inventory(collection: Collection, threshold_qty: int, cutoff_date: str):
    cutoff = datetime.fromisoformat(cutoff_date)
    query = {
        "quantity": {"$gt": threshold_qty},
        "last_sale_date": {"$lt": cutoff.isoformat()}
    }
    return list(collection.find(query, {"_id": 0}))

def sample_tags(collection: Collection, size: int = 5):
    return list(collection.aggregate([{"$sample": {"size": size}}]))

def missing_or_duplicate_tags(collection: Collection, tag_field="tag_number"):
    tags = [doc[tag_field] for doc in collection.find({}, {tag_field: 1, "_id": 0}) if tag_field in doc]
    duplicates = [t for t in set(tags) if tags.count(t) > 1]
    missing = []  # can extend if sequential tag logic known
    return {"duplicates": duplicates, "missing": missing}

def random_price_sample(collection: Collection, min_value: float, size: int = 5):
    return list(collection.aggregate([
        {"$match": {"extended_value": {"$gt": min_value}}},
        {"$sample": {"size": size}}
    ]))

def nrv_test(collection: Collection):
    query = {"$expr": {"$gt": ["$unit_cost", "$net_realizable_value"]}}
    return list(collection.find(query, {"_id": 0}))
