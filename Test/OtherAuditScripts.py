import pandas as pd
from datetime import datetime

def merge_and_list_increased_items(last_year_file, this_year_file, min_unit_cost, min_percent_increase):
    """
    Merge last year's and this year's inventory files, list items with unit cost > min_unit_cost
    and increased by more than min_percent_increase.
    """
    last_df = pd.read_csv(last_year_file)
    this_df = pd.read_csv(this_year_file)
    merged = pd.merge(this_df, last_df, on='itemId', suffixes=('_this', '_last'))
    merged['unit_cost_increase'] = merged['unitPrice_this'] - merged['unitPrice_last']
    merged['percent_increase'] = (merged['unit_cost_increase'] / merged['unitPrice_last']) * 100
    result = merged[
        (merged['unitPrice_this'] > min_unit_cost) &
        (merged['percent_increase'] > min_percent_increase)
    ]
    return result[['itemId', 'description_this', 'unitPrice_last', 'unitPrice_this', 'percent_increase']]

def list_excess_inventory_and_obsolete(inventory_file, sales_file, sales_period_start, sales_period_end, obsolete_date):
    """
    List inventory quantities on hand in excess of units sold during a period.
    List items with last sales date prior to obsolete_date.
    """
    inv_df = pd.read_csv(inventory_file)
    sales_df = pd.read_csv(sales_file)
    sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
    period_sales = sales_df[
        (sales_df['sale_date'] >= pd.to_datetime(sales_period_start)) &
        (sales_df['sale_date'] <= pd.to_datetime(sales_period_end))
    ]
    sales_qty = period_sales.groupby('itemId')['quantity'].sum().reset_index()
    merged = pd.merge(inv_df, sales_qty, on='itemId', how='left', suffixes=('_inv', '_sold'))
    merged['quantity_sold'] = merged['quantity'].fillna(0)
    excess = merged[merged['quantity_inv'] > merged['quantity_sold']]
    # Obsolete items
    last_sales = sales_df.groupby('itemId')['sale_date'].max().reset_index()
    merged2 = pd.merge(inv_df, last_sales, on='itemId', how='left')
    obsolete = merged2[merged2['sale_date'] < pd.to_datetime(obsolete_date)]
    return excess[['itemId', 'description', 'quantity_inv', 'quantity_sold']], obsolete[['itemId', 'description', 'sale_date']]

def sample_inventory_tags(inventory_file, sample_size):
    """
    Select a sample of inventory tag numbers and print the sample selection.
    """
    df = pd.read_csv(inventory_file)
    sample = df.sample(n=sample_size)
    return sample['tag_number'].tolist()

def scan_tag_sequence(inventory_file):
    """
    Scan the sequence of inventory tag numbers and print any missing or duplicate numbers.
    """
    df = pd.read_csv(inventory_file)
    tags = df['tag_number'].sort_values().tolist()
    missing = []
    duplicates = []
    seen = set()
    for i in range(tags[0], tags[-1] + 1):
        if i not in tags:
            missing.append(i)
    for tag in tags:
        if tag in seen:
            duplicates.append(tag)
        else:
            seen.add(tag)
    return missing, duplicates

# Functions available:
# - merge_and_list_increased_items
# - list_excess_inventory_and_obsolete
# - sample_inventory_tags
# - scan_tag_sequence
