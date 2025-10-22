from pymongo import MongoClient, UpdateOne
from pymongo.errors import ServerSelectionTimeoutError
import pandas as pd
import random
from datetime import datetime


MONGO_URI = "mongodb+srv://Aguilar:Aguilar21@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
DB_NAME = 'myDatabase'

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

def create_normalized_collections(db):
    """
    Create the three new normalized collections: items, categories, inventory
    """
    print("Creating normalized collections...")
    
    # Create collections (they will be created when first document is inserted)
    items_collection = db['items']
    categories_collection = db['categories']
    inventory_collection = db['inventory']
    
    # Create indexes for better performance (with error handling)
    try:
        items_collection.create_index("itemId", unique=True)
        print("Created unique index on items.itemId")
    except Exception as e:
        print(f"Warning: Could not create unique index on items.itemId: {e}")
        # Create non-unique index instead
        items_collection.create_index("itemId")
        print("Created non-unique index on items.itemId")
    
    try:
        categories_collection.create_index("categoryId", unique=True)
        print("Created unique index on categories.categoryId")
    except Exception as e:
        print(f"Warning: Could not create unique index on categories.categoryId: {e}")
        # Create non-unique index instead
        categories_collection.create_index("categoryId")
        print("Created non-unique index on categories.categoryId")
    
    try:
        inventory_collection.create_index("itemId")
        print("Created index on inventory.itemId")
    except Exception as e:
        print(f"Warning: Could not create index on inventory.itemId: {e}")
    
    print("Normalized collections created successfully!")
    return items_collection, categories_collection, inventory_collection

def import_from_existing_collections(db, source_collections=['Storage', 'CPU', 'GPU']):
    """
    Import data from existing collections (Storage, CPU, GPU) into normalized schema
    """
    print(f"Importing data from existing collections: {source_collections}")
    
    # Get the normalized collections
    items_collection = db['items']
    categories_collection = db['categories']
    inventory_collection = db['inventory']
    
    # Clear existing data in normalized collections
    items_collection.drop()
    categories_collection.drop()
    inventory_collection.drop()
    
    # Recreate indexes with error handling
    try:
        items_collection.create_index("itemId", unique=True)
    except Exception as e:
        print(f"Warning: Could not create unique index on items.itemId: {e}")
        items_collection.create_index("itemId")
    
    try:
        categories_collection.create_index("categoryId", unique=True)
    except Exception as e:
        print(f"Warning: Could not create unique index on categories.categoryId: {e}")
        categories_collection.create_index("categoryId")
    
    try:
        inventory_collection.create_index("itemId")
    except Exception as e:
        print(f"Warning: Could not create index on inventory.itemId: {e}")
    
    total_imported = 0
    
    for collection_name in source_collections:
        if collection_name not in db.list_collection_names():
            print(f"Warning: Collection '{collection_name}' not found, skipping...")
            continue
            
        source_collection = db[collection_name]
        docs = list(source_collection.find({}))
        
        print(f"Processing {len(docs)} documents from '{collection_name}' collection...")
        
        for doc in docs:
            item_id = doc.get('itemId')
            if not item_id:
                continue
            
            # Collection 1: Items (itemId, name)
            try:
                # Check if item already exists to avoid duplicates
                existing_item = items_collection.find_one({'itemId': item_id})
                if not existing_item:
                    items_collection.insert_one({
                        'itemId': item_id,
                        'name': doc.get('description', '')
                    })
            except Exception as e:
                print(f"Error inserting item {item_id}: {e}")
                continue
            
            # Collection 2: Categories (shared category info)
            category_id = f"{doc.get('category', '')}_{doc.get('supplier', '')}"
            existing_category = categories_collection.find_one({'categoryId': category_id})
            
            if not existing_category:
                try:
                    categories_collection.insert_one({
                        'categoryId': category_id,
                        'category': doc.get('category', ''),
                        'description': f"{doc.get('category', '')} items from {doc.get('supplier', '')}",
                        'supplier': doc.get('supplier', '')
                    })
                except Exception as e:
                    print(f"Error inserting category {category_id}: {e}")
            
            # Collection 3: Inventory (quantity, unitPrice)
            try:
                inventory_collection.insert_one({
                    'itemId': item_id,
                    'quantity': doc.get('quantity', 0),
                    'unitPrice': doc.get('unitPrice', 0),
                    'auditDate': doc.get('auditDate', datetime.now().strftime('%Y-%m-%d'))
                })
            except Exception as e:
                print(f"Error inserting inventory for {item_id}: {e}")
                continue
            
            total_imported += 1
    
    print(f"\nImport completed! Total items imported: {total_imported}")
    print(f"Items collection: {items_collection.count_documents({})} documents")
    print(f"Categories collection: {categories_collection.count_documents({})} documents")
    print(f"Inventory collection: {inventory_collection.count_documents({})} documents")

def query_normalized_data(db, sample_size=None, threshold_value=None):
    """
    Query the normalized data with optional filtering
    """
    pipeline = [
        {
            '$lookup': {
                'from': 'inventory',
                'localField': 'itemId',
                'foreignField': 'itemId',
                'as': 'inventory_info'
            }
        },
        {
            '$unwind': '$inventory_info'
        },
        {
            '$lookup': {
                'from': 'categories',
                'let': {'item_category': '$inventory_info.category'},
                'pipeline': [
                    {'$match': {'$expr': {'$eq': ['$category', '$$item_category']}}}
                ],
                'as': 'category_info'
            }
        },
        {
            '$addFields': {
                'extendedValue': {
                    '$multiply': ['$inventory_info.unitPrice', '$inventory_info.quantity']
                }
            }
        }
    ]
    
    # Add filtering if specified
    if threshold_value is not None:
        pipeline.append({
            '$match': {'extendedValue': {'$gt': threshold_value}}
        })
    
    # Add sampling if specified
    if sample_size is not None:
        pipeline.append({'$sample': {'size': sample_size}})
    
    results = list(db['items'].aggregate(pipeline))
    return results

def perform_price_testing_audit_normalized(db, sample_size, threshold_value):
    """
    Perform price testing audit on normalized data
    """
    print(f"Performing audit with sample size: {sample_size}, threshold: ${threshold_value}")
    
    # Get high value items
    high_value_items = query_normalized_data(db, threshold_value=threshold_value)
    
    print(f"Items exceeding ${threshold_value}: {len(high_value_items)}")
    
    # Sample items
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
        inventory = item.get('inventory_info', {})
        category = item.get('category_info', [{}])[0] if item.get('category_info') else {}
        
        print(f"{i}. {item.get('itemId', 'N/A')} - {item.get('name', 'N/A')}")
        print(f"   Unit Price: ${inventory.get('unitPrice', 0):.2f}")
        print(f"   Quantity: {inventory.get('quantity', 0)}")
        print(f"   Extended Value: ${item.get('extendedValue', 0):.2f}")
        print(f"   Category: {category.get('category', 'N/A')}")
        print(f"   Supplier: {category.get('supplier', 'N/A')}")
        print("   " + "-" * 30)
        total_sampled_value += item.get('extendedValue', 0)
    
    print(f"\nTotal Sampled Value: ${total_sampled_value:.2f}")
    return sampled_items

def export_audit_results_normalized(sampled_items, filename="audit_results_normalized.csv"):
    """
    Export audit results from normalized data
    """
    export_data = []
    for item in sampled_items:
        inventory = item.get('inventory_info', {})
        category = item.get('category_info', [{}])[0] if item.get('category_info') else {}
        
        export_data.append({
            'Item ID': item.get('itemId', 'N/A'),
            'Description': item.get('name', 'N/A'),
            'Unit Price': inventory.get('unitPrice', 0),
            'Quantity': inventory.get('quantity', 0),
            'Extended Value': item.get('extendedValue', 0),
            'Category': category.get('category', 'N/A'),
            'Supplier': category.get('supplier', 'N/A'),
            'Audit Date': inventory.get('auditDate', datetime.now().strftime('%Y-%m-%d'))
        })
    
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    print(f"Results exported to {filename}")
    return df

def verify_normalized_data_integrity(db):
    """
    Verify data integrity in normalized collections
    """
    print("\n=== NORMALIZED DATA INTEGRITY CHECK ===")
    
    items_count = db['items'].count_documents({})
    categories_count = db['categories'].count_documents({})
    inventory_count = db['inventory'].count_documents({})
    
    print(f"Items collection: {items_count} documents")
    print(f"Categories collection: {categories_count} documents")
    print(f"Inventory collection: {inventory_count} documents")
    
    # Check for orphaned inventory records
    pipeline = [
        {'$lookup': {
            'from': 'items',
            'localField': 'itemId',
            'foreignField': 'itemId',
            'as': 'item_info'
        }},
        {'$match': {'item_info': []}},
        {'$count': 'orphaned_count'}
    ]
    
    orphaned_result = list(db['inventory'].aggregate(pipeline))
    orphaned_count = orphaned_result[0]['orphaned_count'] if orphaned_result else 0
    
    print(f"Orphaned inventory records: {orphaned_count}")
    
    # Calculate total inventory value
    pipeline = [
        {'$lookup': {
            'from': 'items',
            'localField': 'itemId',
            'foreignField': 'itemId',
            'as': 'item_info'
        }},
        {'$unwind': '$item_info'},
        {'$project': {
            'totalValue': {'$multiply': ['$unitPrice', '$quantity']}
        }},
        {'$group': {
            '_id': None,
            'totalInventoryValue': {'$sum': '$totalValue'}
        }}
    ]
    
    result = list(db['inventory'].aggregate(pipeline))
    if result:
        total_value = result[0]['totalInventoryValue']
        print(f"Total Inventory Value: ${total_value:,.2f}")
    
    return items_count

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
    print("=== MONGODB NORMALIZED INVENTORY PRICE TESTING AUDIT ===")
    db = connect_to_mongodb()
    
    # Check if normalized collections exist
    collections = db.list_collection_names()
    normalized_collections = ['items', 'categories', 'inventory']
    
    if not all(col in collections for col in normalized_collections):
        print("Normalized collections not found. Creating them...")
        create_normalized_collections(db)
        
        # Import data from existing collections
        import_choice = input("Do you want to import data from existing collections (Storage, CPU, GPU)? (Y/N): ").upper()
        if import_choice == "Y":
            import_from_existing_collections(db)
        else:
            print("Skipping data import. You can run the import later.")
    else:
        print("Normalized collections found!")
        verify_normalized_data_integrity(db)
    
    # Perform audit
    sample_size = get_user_input("\nEnter sample size: ", input_type=int, validation=lambda x: x > 0)
    threshold_value = get_user_input("Enter threshold value: ", input_type=float, validation=lambda x: x >= 0)
    
    print(f"\nSample size: {sample_size}")
    print(f"Threshold value: ${threshold_value}")
    
    sampled_items = perform_price_testing_audit_normalized(db, sample_size, threshold_value)
    
    export_confirm = input("\nWould you like to export the results? (Y/N): ").upper()
    if export_confirm == "Y":
        export_audit_results_normalized(sampled_items)
    
    print("\n=== AUDIT COMPLETE ===")
    print(f"Successfully sampled {len(sampled_items)} items for price testing")

if __name__ == "__main__":
    main()
