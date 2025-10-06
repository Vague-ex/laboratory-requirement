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
        print("Successfully connected to MongoDB")
        return db
    except ServerSelectionTimeoutError as err:
        print("Could not connect to MongoDB:", err)
        exit(1)

def cleanup_extended_values(collection):
    collection.update_many(
        {}, 
        {'$unset': {'extendedValue': ''}}
    )
    print("Extended values cleaned up from database")

def verify_data(collection):
    total_count = collection.count_documents({})
    print(f"Total items in database: {total_count}")
    
    print("\nSample items:")
    for item in collection.find({}, {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1})():
        print(f"- {item.get('itemId', 'N/A')}: {item.get('description', 'N/A')} - ${item.get('unitPrice', 0)} x {item.get('quantity', 0)}")
    
    return total_count

def calculate_extended_values(collection):
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

def perform_price_testing_audit(collection, sample_size, threshold_value):
    calculate_extended_values(collection)
    
    high_value_items = list(collection.find(
        {'extendedValue': {'$gt': threshold_value}},
        {'itemId': 1, 'description': 1, 'unitPrice': 1, 'quantity': 1, 'extendedValue': 1, 'category': 1, 'supplier': 1}
    ))
    
    print(f"Items exceeding ${threshold_value}: {len(high_value_items)}")
    
    
    if len(high_value_items) <= sample_size:
        sampled_items = high_value_items
    else:
        sampled_items = random.sample(high_value_items, sample_size)
    
    
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

def get_user_input(prompt, input_type=float, validation=None):
    while True:
        try:
            user_input = input_type(input(prompt))
            if validation and not validation(user_input):
                print("Invalid input. Please try again.")
                continue
            return user_input
        except ValueError:
            print("Please enter a valid number")

def main():
    print("=== MONGODB INVENTORY PRICE TESTING AUDIT ===")
    db = connect_to_mongodb()
    available_collections = db.list_collection_names()
    if not available_collections:
        print("No collections found in the database.")
        return
    print("\nAvailable collections:")
    for i, collection_name in enumerate(available_collections, 1):
        print(f"{i}. {collection_name}")
    
    collection_choice = get_user_input(
        f"\nSelect collection (1-{len(available_collections)}): ",
        input_type=int,
        validation=lambda x: 1 <= x <= len(available_collections)
    )
    selected_collection = available_collections[collection_choice - 1]
    
    sample_size = get_user_input("\nEnter sample size: ", input_type=int,validation=lambda x: x > 0)
    threshold_value = get_user_input("Enter threshold value: ", input_type=float, validation=lambda x: x >= 0)
    print(f"\nSelected collection: {selected_collection}")
    print(f"Sample size: {sample_size}")
    print(f"Threshold value: ${threshold_value}")
    
    collection_obj = db[selected_collection]
    verify_data(collection_obj)
    sampled_items = perform_price_testing_audit(collection_obj, sample_size, threshold_value)
    
    export_confirm = input("\nWould you like to export the results? (Y/N): ").upper()
    if export_confirm == "Y":
        export_audit_results(sampled_items)
        #cleanup_extended_values(collection_obj)
        
    print("\n=== AUDIT COMPLETE ===")
    print(f"\n\nSuccessfully sampled {len(sampled_items)} items for price testing")
    
if __name__ == "__main__":
    main()