import tkinter as tk
from tkinter import ttk, messagebox
from PriceTestAuditScript import (
    perform_price_testing_audit,
    export_audit_results,
    find_low_stock_items,
    find_high_unit_price_items
)

def run_audit():
    try:
        audit_type = audit_type_var.get()
        sample_size = int(sample_size_var.get())
        threshold_value = float(threshold_var.get())
        # Choose audit script
        if audit_type == "Price Testing":
            sampled_items = perform_price_testing_audit(sample_size, threshold_value)
            df = export_audit_results(sampled_items, filename=None)
            status_var.set(f"Sampled {len(sampled_items)} items above ${threshold_value}")
        elif audit_type == "Low Stock":
            low_stock_items = find_low_stock_items(stock_threshold=int(threshold_var.get()))
            df = export_audit_results(low_stock_items, filename=None)
            status_var.set(f"Found {len(low_stock_items)} items below stock {threshold_var.get()}")
        elif audit_type == "High Unit Price":
            high_price_items = find_high_unit_price_items(unit_price_threshold=threshold_value)
            df = export_audit_results(high_price_items, filename=None)
            status_var.set(f"Found {len(high_price_items)} items above unit price ${threshold_var.get()}")
        else:
            status_var.set("Unknown audit type.")
            return
        # Update table
        for row in tree.get_children():
            tree.delete(row)
        for item in df.to_dict(orient='records'):
            tree.insert('', 'end', values=(
                item['Item ID'],
                item['Description'],
                item['Unit Price'],
                item['Quantity'],
                item['Extended Value'],
                item['Category'],
                item['Supplier'],
                item['Audit Date']
            ))
    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_var.set("Error running audit.")

root = tk.Tk()
root.title("Inventory Audit Dashboard")
root.configure(bg="#f8f9fa")

title_label = tk.Label(root, text="Inventory Audit Dashboard", font=("Segoe UI", 20, "bold"), bg="#f8f9fa", fg="#0d6efd")
title_label.pack(pady=(20,10))

frame = ttk.Frame(root, padding=15)
frame.pack(fill='x', padx=20)

audit_type_var = tk.StringVar(value="Price Testing")
ttk.Label(frame, text="Audit Type:").grid(row=0, column=0, sticky='w')
audit_type_menu = ttk.Combobox(frame, textvariable=audit_type_var, state="readonly",
    values=["Price Testing", "Low Stock", "High Unit Price"])
audit_type_menu.grid(row=0, column=1, padx=5)

ttk.Label(frame, text="Sample Size:").grid(row=0, column=2, sticky='w')
sample_size_var = tk.StringVar(value='3')
ttk.Entry(frame, textvariable=sample_size_var, width=8).grid(row=0, column=3, padx=5)

ttk.Label(frame, text="Threshold Value:").grid(row=0, column=4, sticky='w')
threshold_var = tk.StringVar(value='5000')
ttk.Entry(frame, textvariable=threshold_var, width=10).grid(row=0, column=5, padx=5)

ttk.Button(frame, text="Run Audit", command=run_audit).grid(row=0, column=6, padx=10)

table_frame = ttk.Frame(root)
table_frame.pack(fill='both', expand=True, padx=20, pady=10)

columns = ['Item ID', 'Description', 'Unit Price', 'Quantity', 'Extended Value', 'Category', 'Supplier', 'Audit Date']
tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor='center')
tree.pack(side='left', fill='both', expand=True)

scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side='right', fill='y')

status_var = tk.StringVar(value="Ready.")
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief='sunken', anchor='w', bg="#e9ecef", font=("Segoe UI", 10))
status_bar.pack(fill='x', padx=20, pady=(0,10))

root.mainloop()
