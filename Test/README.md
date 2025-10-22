# Inventory Price Testing Lab Profe4

python script for auditing inventory data stored in MongoDB. Identifies high-value items for price testing and export the results.

## What It Does

- Connects to your MongoDB database
- Calculates extended values (unit price × quantity)
- Finds items exceeding a value threshold
- Randomly samples items for audit
- Exports results to CSV

## Quick Start

1. **Prerequisites**
   - Python 3
   - MongoDB database with inventory data
   - Required packages: `pymongo`, `pandas`

2. **Install Dependencies**
   ```bash
   pip install pymongo pandas
   ```

3. **Run the Script**
   ```bash
   python Auditscriptnew.py 
   ```

4. **Selections when runnning script**
   - Select which collection to audit
   - Choose how many items to sample
   - Set your value threshold
   - Audit results

*Make sure MongoDB connection string in the script points to your actual database.*
## Output

The script generates a CSV file with:
- Item details (ID, description, price, quantity)
- Calculated extended values
- Category and supplier information
- Audit date

---


