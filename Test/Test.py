from pymongo import MongoClient
import pandas as pd
import random
from datetime import datetime


# mongodb+srv://Aguilar:Aguilar1@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority&appName=PROFE3
client = MongoClient("mongodb+srv://Aguilar:Aguilar1@profe3.pdrabfb.mongodb.net/?retryWrites=true&w=majority&appName=PROFE3")
db = client['inventoryaudit']
collection = db['inventoryitems']

def create_sample_dataset():
    """Create sample inventory dataset"""
    
    sample_data = [
        {
            "itemId": "INV001",
            "description": "Laptop Computer",
            "unitPrice": 899.99,
            "quantity": 25,
            "category": "Electronics",
            "supplier": "TechCorp"
        },
        {
            "itemId": "INV002",
            "description": "Office Chair",
            "unitPrice": 249.50,
            "quantity": 40,
            "category": "Furniture",
            "supplier": "OfficeSupplies Inc"
        },
        {
            "itemId": "INV003",
            "description": "Printer",
            "unitPrice": 299.99,
            "quantity": 30,
            "category": "Electronics",
            "supplier": "TechCorp"
        },
        {
            "itemId": "INV004",
            "description": "Desk",
            "unitPrice": 450.00,
            "quantity": 15,
            "category": "Furniture",
            "supplier": "OfficeSupplies Inc"
        },
        {
            "itemId": "INV005",
            "description": "Monitor",
            "unitPrice": 199.99,
            "quantity": 50,
            "category": "Electronics",
            "supplier": "TechCorp"
        },
        {
            "itemId": "INV006",
            "description": "Keyboard",
            "unitPrice": 49.99,
            "quantity": 100,
            "category": "Electronics",
            "supplier": "Accessories Ltd"
        },
        {
            "itemId": "INV007",
            "description": "Filing Cabinet",
            "unitPrice": 189.95,
            "quantity": 20,
            "category": "Furniture",
            "supplier": "OfficeSupplies Inc"
        },
        {
            "itemId": "INV008",
            "description": "Server Rack",
            "unitPrice": 1250.00,
            "quantity": 8,
            "category": "Electronics",
            "supplier": "EnterpriseTech"
        },
        {
            "itemId": "INV009",
            "description": "Desk Lamp",
            "unitPrice": 29.99,
            "quantity": 75,
            "category": "Furniture",
            "supplier": "Accessories Ltd"
        },
        {
            "itemId": "INV010",
            "description": "Network Switch",
            "unitPrice": 399.99,
            "quantity": 12,
            "category": "Electronics",
            "supplier": "EnterpriseTech"
        }
    ]
    
    # Clear existing data (optional)
    collection.delete_many({})
    
    # Insert sample data
    result = collection.insert_many(sample_data)
    print(f"Inserted {len(result.inserted_ids)} documents")
    
    return result.inserted_ids

# Create the dataset
create_sample_dataset()

def import_from_csv(csv_file_path):
    """Import inventory data from CSV file"""
    
    # Read CSV file
    df = pd.read_csv(csv_file_path)
    
    # Convert to dictionary records
    data = df.to_dict('records')
    
    # Insert into MongoDB
    result = collection.insert_many(data)
    print(f"Imported {len(result.inserted_ids)} items from CSV")
    
    return result.inserted_ids

# Example usage if you have a CSV file:
# import_from_csv("inventory_data.csv")

def verify_data():
    """Verify that data was imported correctly"""
    
    # Count total documents
    total_count = collection.count_documents({})
    print(f"Total items in database: {total_count}")
    
    # Show first few documents
    print("\nFirst 5 items:")
    for item in collection.find().limit(5):
        print(f"- {item['itemId']}: {item['description']} - ${item['unitPrice']} x {item['quantity']}")
    
    return total_count

# Verify the data
verify_data()

def calculate_extended_values():
    """Calculate and update extended values for all items"""
    
    # Get all items
    items = list(collection.find({}))
    
    for item in items:
        extended_value = item['unitPrice'] * item['quantity']
        
        # Update the document with extended value
        collection.update_one(
            {'_id': item['_id']},
            {'$set': {'extendedValue': extended_value}}
        )
    
    print("Extended values calculated for all items")

def perform_price_testing_audit(sample_size=3, threshold_value=5000):
    """Main function to perform price testing audit"""
    
    # Step 1: Calculate extended values
    calculate_extended_values()
    
    # Step 2: Get items exceeding threshold
    high_value_items = list(collection.find({
        'extendedValue': {'$gt': threshold_value}
    }))
    
    print(f"Items exceeding ${threshold_value}: {len(high_value_items)}")
    
    # Step 3: Random sampling
    if len(high_value_items) <= sample_size:
        sampled_items = high_value_items
        print("Sample size larger than available items, selecting all")
    else:
        sampled_items = random.sample(high_value_items, sample_size)
    
    # Step 4: Display results
    print(f"\n=== SELECTED SAMPLE FOR PRICE TESTING ===")
    print(f"Sample Size: {sample_size}")
    print(f"Threshold: ${threshold_value}")
    print("=" * 50)
    
    total_sampled_value = 0
    for i, item in enumerate(sampled_items, 1):
        print(f"{i}. {item['itemId']} - {item['description']}")
        print(f"   Unit Price: ${item['unitPrice']:.2f}")
        print(f"   Quantity: {item['quantity']}")
        print(f"   Extended Value: ${item['extendedValue']:.2f}")
        print(f"   Category: {item['category']}")
        print("   " + "-" * 30)
        
        total_sampled_value += item['extendedValue']
    
    print(f"\nTotal Sampled Value: ${total_sampled_value:.2f}")
    
    return sampled_items

def export_audit_results(sampled_items, filename="audit_results.csv"):
    """Export audit results to CSV"""
    
    export_data = []
    for item in sampled_items:
        export_data.append({
            'Item ID': item['itemId'],
            'Description': item['description'],
            'Unit Price': item['unitPrice'],
            'Quantity': item['quantity'],
            'Extended Value': item['extendedValue'],
            'Category': item['category'],
            'Supplier': item.get('supplier', 'N/A'),
            'Audit Date': datetime.now().strftime('%Y-%m-%d')
        })
    
    df = pd.DataFrame(export_data)
    df.to_csv(filename, index=False)
    print(f"Results exported to {filename}")
    
    return df




# Main execution
if __name__ == "__main__":
    # Set your parameters
    SAMPLE_SIZE = 3
    THRESHOLD_VALUE = 5000
    
    print("=== MONGODB INVENTORY PRICE TESTING AUDIT ===")
    
    # Perform the audit
    sampled_items = perform_price_testing_audit(SAMPLE_SIZE, THRESHOLD_VALUE)
    
    # Export results
    export_audit_results(sampled_items)
    
    # Show summary
    print("\n=== AUDIT COMPLETE ===")
    print(f"Successfully sampled {len(sampled_items)} items for price testing")

if __name__ == "__main__":
    # Your parameters here
    perform_price_testing_audit(sample_size=3, threshold_value=5000)