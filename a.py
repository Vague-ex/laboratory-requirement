from pymongo import MongoClient, UpdateOne
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
import random
from datetime import datetime


MONGO_URI = "mongodb+srv://Aguilar:Aguilar21@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
DB_NAME = 'inventoryaudit'

def connect_to_mongodb():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
        db = client[DB_NAME]
        client.admin.command('ping')
        print("Connected to MongoDB")
        return db
    except ServerSelectionTimeoutError as err:
        print("Could not connect to MongoDB:", err)
        raise SystemExit(1)

def cleanup_extended_values(collection):
    collection.update_many({}, {'$unset': {'extendedValue': ''}})
    print("Cleared 'extendedValue' on collection")

def calculate_extended_values(collection):
    items = collection.find({}, {'_id': 1, 'unitPrice': 1, 'quantity': 1})
    ops = []
    for it in items:
        ev = (it.get('unitPrice') or 0) * (it.get('quantity') or 0)
        ops.append(UpdateOne({'_id': it['_id']}, {'$set': {'extendedValue': ev}}))
    if ops:
        collection.bulk_write(ops)

def perform_price_testing_audit(collection, sample_size, threshold_value):
    calculate_extended_values(collection)
    query = {'extendedValue': {'$gt': threshold_value}}
    proj = {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1, 'extendedValue': 1, 'category': 1, 'supplier': 1}
    items = list(collection.find(query, proj))
    if not items:
        print("No items exceed threshold.")
        return []
    sampled = items if len(items) <= sample_size else random.sample(items, sample_size)
    total = sum(it.get('extendedValue', 0) for it in sampled)
    print(f"Selected {len(sampled)} items (total sampled value: ${total:,.2f})")
    return sampled

def export_audit_results(sampled_items, filename="audit_results.csv"):
    df = pd.DataFrame([
        {
            'Item ID': it.get('itemId', 'N/A'),
            'Description': it.get('description', 'N/A'),
            'Unit Price': it.get('unitPrice', 0),
            'Quantity': it.get('quantity', 0),
            'Extended Value': it.get('extendedValue', 0),
            'Category': it.get('category', 'N/A'),
            'Supplier': it.get('supplier', 'N/A'),
            'Audit Date': datetime.now().strftime('%Y-%m-%d')
        }
        for it in sampled_items
    ])
    if filename:
        df.to_csv(filename, index=False)
        print(f"Exported {len(df)} rows to {filename}")
    return df

def prompt(prompt_text, cast=str, validate=None, default=None):
    while True:
        try:
            raw = input(prompt_text).strip()
            if raw == "" and default is not None:
                return default
            val = cast(raw)
            if validate and not validate(val):
                print("Invalid value; try again.")
                continue
            return val
        except Exception:
            print("Invalid input; try again.")

def main():
    print("=== MONGODB INVENTORY PRICE TESTING AUDIT ===")
    db = connect_to_mongodb()
    collections = db.list_collection_names()
    if not collections:
        print("No collections found.")
        return
    print("\nAvailable collections:")
    for i, name in enumerate(collections, 1):
        print(f"{i}. {name}")
    idx = prompt(f"Select collection (1-{len(collections)}): ", cast=int, validate=lambda x: 1 <= x <= len(collections))
    coll_name = collections[idx - 1]
    sample_size = prompt("Sample size [default 50]: ", cast=int, default=50, validate=lambda x: x > 0)
    threshold = prompt("Threshold value [$] [default 1000]: ", cast=float, default=1000.0, validate=lambda x: x >= 0)
    coll = db[coll_name]
    sampled = perform_price_testing_audit(coll, sample_size, threshold)
    if not sampled:
        return
    if prompt("Export results to CSV? (Y/n): ", cast=str, default="Y").upper().startswith("Y"):
        fname = f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_audit_results(sampled, filename=fname)
    else:
        cleanup_extended_values(coll)
    print("=== AUDIT COMPLETE ===")
    print(f"Sampled {len(sampled)} items from '{coll_name}'")

if __name__ == "__main__":
    main()