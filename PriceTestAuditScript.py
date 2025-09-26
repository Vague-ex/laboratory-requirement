from pymongo import MongoClient, UpdateOne
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
import random
from datetime import datetime


MONGO_URI = "mongodb+srv://Aguilar:Aguilar21@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
DB_NAME = 'inventoryaudit'
COLLECTION_NAME = 'CPU'

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Test connection
    client.admin.command('ping')
except ServerSelectionTimeoutError as err:
    print("Could not connect to MongoDB:", err)
    exit(1)

def import_from_csv(csv_file_path):
    """Import inventory data from CSV file"""
    df = pd.read_csv(csv_file_path)
    data = df.to_dict('records')
    result = collection.insert_many(data)
    print(f"Imported {len(result.inserted_ids)} items from CSV")
    return result.inserted_ids

def verify_data(limit=5):
    """Verify that data was imported correctly"""
    total_count = collection.count_documents({})
    print(f"Total items in database: {total_count}")
    print("\nFirst 5 items:")
    for item in collection.find({}, {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1}).limit(limit):
        print(f"- {item.get('itemId', 'N/A')}: {item.get('description', 'N/A')} - ${item.get('unitPrice', 0)} x {item.get('quantity', 0)}")
    return total_count

def calculate_extended_values():
    """Calculate and update extended values for all items"""
    items = collection.find({}, {'_id': 1, 'unitPrice': 1, 'quantity': 1})
    bulk_ops = []
    for item in items:
        extended_value = item.get('unitPrice', 0) * item.get('quantity', 0)
        bulk_ops.append(
            UpdateOne(
                {'_id': item['_id']},
                {'$set': {'extendedValue': extended_value}}
            )
        )
    if bulk_ops:
        collection.bulk_write(bulk_ops)
    print("Extended values calculated for all items")

def perform_price_testing_audit(sample_size=3, threshold_value=5000):
    """Main function to perform price testing audit"""
    calculate_extended_values()
    high_value_items = list(collection.find(
        {'extendedValue': {'$gt': threshold_value}},
        {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1, 'extendedValue': 1, 'category': 1, 'supplier': 1}
    ))
    print(f"Items exceeding ${threshold_value}: {len(high_value_items)}")
    sampled_items = high_value_items if len(high_value_items) <= sample_size else random.sample(high_value_items, sample_size)
    print(f"\n=== SELECTED SAMPLE FOR PRICE TESTING ===")
    print(f"Sample Size: {sample_size}")
    print(f"Threshold: ${threshold_value}")
    print("=" * 50)
    total_sampled_value = 0
    for i, item in enumerate(sampled_items, 1):
        print(f"{i}. {item.get('itemId', 'N/A')} - {item.get('description', 'N/A')}")
        print(f"   Unit Price: ${item.get('unitPrice', 0):.2f}")
        print(f"   Quantity: {item.get('quantity', 0)}")
        print(f"   Extended Value: ${item.get('extendedValue', 0):.2f}")
        print(f"   Category: {item.get('category', 'N/A')}")
        print("   " + "-" * 30)
        total_sampled_value += item.get('extendedValue', 0)
    print(f"\nTotal Sampled Value: ${total_sampled_value:.2f}")
    return sampled_items

def export_audit_results(sampled_items, filename="audit_results.csv"):
    """Export audit results to CSV"""
    export_data = []
    for item in sampled_items:
        export_data.append({
            'Item ID': item.get('itemId', 'N/A'),
            'Description': item.get('description', 'N/A'),
            'Unit Price': item.get('unitPrice', 0),
            'Quantity': item.get('quantity', 0),
            'Extended Value': item.get('extendedValue', 0),
            'Category': item.get('category', 'N/A'),
            'Supplier': item.get('supplier', 'N/A'),
            'Audit Date': datetime.now().strftime('%Y-%m-%d')
        })
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    print(f"Results exported to {filename}")
    return df

def find_low_stock_items(stock_threshold=10):
    """Find items with quantity below the given threshold"""
    low_stock_items = list(collection.find(
        {'quantity': {'$lt': stock_threshold}},
        {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1, 'extendedValue': 1, 'category': 1, 'supplier': 1}
    ))
    print(f"Items with quantity below {stock_threshold}: {len(low_stock_items)}")
    return low_stock_items

def find_high_unit_price_items(unit_price_threshold=1000):
    """Find items with unit price above the given threshold"""
    high_price_items = list(collection.find(
        {'unitPrice': {'$gt': unit_price_threshold}},
        {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1, 'extendedValue': 1, 'category': 1, 'supplier': 1}
    ))
    print(f"Items with unit price above {unit_price_threshold}: {len(high_price_items)}")
    return high_price_items

if __name__ == "__main__":
    SAMPLE_SIZE = 3
    THRESHOLD_VALUE = 5000
    print("=== MONGODB INVENTORY PRICE TESTING AUDIT ===")
    verify_data()
    sampled_items = perform_price_testing_audit(SAMPLE_SIZE, THRESHOLD_VALUE)
    export_audit_results(sampled_items)
    print("\n=== AUDIT COMPLETE ===")
    print(f"Successfully sampled {len(sampled_items)} items for price testing")