from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import pandas as pd
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Input,
    Label,
    DataTable,
    Select,
    TabbedContent,
    TabPane,
    Tabs,
)

# Reuse backend from a.py
import a as backend


class DashboardPane(TabPane):
    def __init__(self, *, id: str = "dashboard") -> None:
        super().__init__("Dashboard", id=id)

    def compose(self) -> ComposeResult:
        yield Static("MONGODB INVENTORY AUDIT SYSTEM", classes="title")
        yield Static("Connection", classes="section-title")
        yield Static("Status: Checking...", id="conn-status")
        yield Static("Database: -", id="db-name")
        yield Static("Collections found: 0", id="db-colls")
        with Horizontal(classes="actions"):
            yield Button("Run Audit", id="go-config")
            yield Button("Data Integrity", id="go-integrity")
            yield Button("Export Data", id="go-export")


class ConfigPane(TabPane):
    def __init__(self, *, id: str = "config") -> None:
        super().__init__("Configure Audit", id=id)

    def compose(self) -> ComposeResult:
        yield Static("CONFIGURE AUDIT PARAMETERS", classes="title")
        with Vertical():
            yield Label("Available Collections:")
            yield Select([], prompt="Select collection", id="collections")
        with Horizontal():
            yield Label("Sample Size (1-500)")
            yield Input(placeholder="50", id="sample-size")
            yield Label("Threshold ($)")
            yield Input(placeholder="1000", id="threshold")
        yield Static("Preview:", classes="section-title")
        yield Static("Select a collection to see preview.", id="preview")
        with Horizontal(classes="actions"):
            yield Button("Run Audit", variant="success", id="run-audit")
            yield Button("Reset", id="reset-config")


class IntegrityPane(TabPane):
    def __init__(self, *, id: str = "integrity") -> None:
        super().__init__("Data Integrity", id=id)

    def compose(self) -> ComposeResult:
        yield Static("DATA INTEGRITY REPORT", classes="title")
        with Horizontal():
            yield Select([], prompt="Select collection", id="integrity-collections")
            yield Button("Scan", id="scan-integrity")
        self.table = DataTable(id="integrity-table")
        self.table.add_columns("Check Type", "Status", "Count", "Percent")
        yield self.table
        yield Static("Total Inventory Value: $0.00", id="integrity-total")


class ResultsPane(TabPane):
    def __init__(self, *, id: str = "results") -> None:
        super().__init__("Audit Results", id=id)

    def compose(self) -> ComposeResult:
        yield Static("PRICE TESTING AUDIT RESULTS", classes="title")
        yield Static("Collection: - | Items: 0 | Total Sampled Value: $0.00", id="results-meta")
        self.table = DataTable(id="results-table")
        self.table.add_columns("Item ID", "Description", "Price", "Qty", "Value")
        yield self.table
        with Horizontal(classes="actions"):
            yield Button("Refine", id="results-refine")
            yield Button("Export CSV", id="results-export", variant="primary")
            yield Button("New Audit", id="results-new")


class ExportPane(TabPane):
    def __init__(self, *, id: str = "export") -> None:
        super().__init__("Export", id=id)

    def compose(self) -> ComposeResult:
        yield Static("EXPORT COMPLETE", classes="title")
        yield Static("No export yet.", id="export-info")
        with Horizontal(classes="actions"):
            yield Button("Back to Dashboard", id="export-back")


class AuditApp(App):
    CSS = """
    .title { text-align: center; padding: 1 0; content-align: center middle; height: 3; }
    .section-title { padding: 1 0 0 0; color: $accent; }
    .actions { padding: 1; gap: 2; }
    #results-table, #integrity-table { height: 1fr; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.db = None
        self.sampled_items: List[dict] = []
        self.selected_collection: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            yield DashboardPane()
            yield ConfigPane()
            yield IntegrityPane()
            yield ResultsPane()
            yield ExportPane()
        yield Footer()

    def on_mount(self) -> None:
        self._connect_db()

    # Helpers
    def _connect_db(self) -> None:
        conn_status = self.query_one("#conn-status", Static)
        db_name_lbl = self.query_one("#db-name", Static)
        db_colls_lbl = self.query_one("#db-colls", Static)
        try:
            self.db = backend.connect_to_mongodb()
            colls = self.db.list_collection_names()
            conn_status.update("✓ Successfully connected to MongoDB")
            db_name_lbl.update(f"Database: {backend.DB_NAME}")
            db_colls_lbl.update(f"Collections found: {len(colls)}")
            # Populate selects
            self._populate_collections(colls)
        except Exception as e:
            conn_status.update(f"✗ Connection failed: {e}")
            db_name_lbl.update("Database: -")
            db_colls_lbl.update("Collections found: 0")

    def _populate_collections(self, colls: List[str]) -> None:
        self.query_one("#collections", Select).set_options([(c, c) for c in colls])
        self.query_one("#integrity-collections", Select).set_options([(c, c) for c in colls])

    # Events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "go-config":
            self.switch_tab("config")
        elif bid == "go-integrity":
            self.switch_tab("integrity")
        elif bid == "go-export":
            self.switch_tab("export")
        elif bid == "run-audit":
            self._run_audit_from_config()
        elif bid == "reset-config":
            self._reset_config()
        elif bid == "scan-integrity":
            self._scan_integrity()
        elif bid == "results-refine":
            self.switch_tab("config")
        elif bid == "results-export":
            self._export_results()
        elif bid == "results-new":
            self.switch_tab("config")
        elif bid == "export-back":
            self.switch_tab("dashboard")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "collections":
            self._update_preview()

    # Config actions
    def _reset_config(self) -> None:
        self.query_one("#collections", Select).clear()
        if self.db is not None:
            self._populate_collections(self.db.list_collection_names())
        self.query_one("#sample-size", Input).value = ""
        self.query_one("#threshold", Input).value = ""
        self.query_one("#preview", Static).update("Select a collection to see preview.")

    def _update_preview(self) -> None:
        select = self.query_one("#collections", Select)
        name = select.value
        if not name:
            return
        total = 0
        try:
            total = self.db[name].count_documents({}) if self.db is not None else 0
        except Exception:
            total = 0
        sample_str = self.query_one("#sample-size", Input).value or "50"
        threshold_str = self.query_one("#threshold", Input).value or "1000"
        try:
            sample = max(1, min(500, int(sample_str)))
        except Exception:
            sample = 50
        try:
            threshold = max(0.0, float(threshold_str))
        except Exception:
            threshold = 1000.0
        pct = (sample / total * 100) if total else 0
        est = int(max(0, round(total * 0.07)))
        preview = (
            f"AUDIT PREVIEW\n"
            f"• Collection: {name}\n"
            f"• Total items: {total:,}\n"
            f"• Sample size: {sample} items ({pct:.1f}% of total)\n"
            f"• Items above ${threshold:,.2f}: ~{est} estimated\n"
        )
        self.query_one("#preview", Static).update(preview)

    def _run_audit_from_config(self) -> None:
        select = self.query_one("#collections", Select)
        name = select.value
        if not name:
            self.notify("Please select a collection.")
            return
        sample_str = self.query_one("#sample-size", Input).value or "50"
        threshold_str = self.query_one("#threshold", Input).value or "1000"
        try:
            sample_size = max(1, min(500, int(sample_str)))
            threshold = max(0.0, float(threshold_str))
        except Exception:
            self.notify("Invalid inputs; using defaults (50, $1000).")
            sample_size, threshold = 50, 1000.0
        try:
            coll = self.db[name]
            sampled = backend.perform_price_testing_audit(coll, sample_size, threshold)
        except Exception as e:
            self.notify(f"Audit error: {e}")
            return
        self.selected_collection = name
        self.sampled_items = sampled
        self._render_results()
        self.switch_tab("results")

    # Integrity actions
    def _scan_integrity(self) -> None:
        sel = self.query_one("#integrity-collections", Select)
        name = sel.value
        if not name:
            self.notify("Please select a collection.")
            return
        coll = self.db[name]
        total_count = coll.count_documents({})
        checks = {
            "Missing ItemID": coll.count_documents({'itemId': {'$exists': False}}),
            "Missing Price": coll.count_documents({'unitPrice': {'$exists': False}}),
            "Missing Quantity": coll.count_documents({'quantity': {'$exists': False}}),
            "Negative Price": coll.count_documents({'unitPrice': {'$lt': 0}}),
            "Negative Qty": coll.count_documents({'quantity': {'$lt': 0}}),
        }
        table = self.query_one("#integrity-table", DataTable)
        table.clear()
        for label, count in checks.items():
            percent = (count / total_count * 100) if total_count else 0
            status = "PASS" if count == 0 else "WARN"
            table.add_row(label, status, str(count), f"{percent:.1f}%")
        pipeline = [
            {'$match': {'unitPrice': {'$exists': True}, 'quantity': {'$exists': True}}},
            {'$project': {'totalValue': {'$multiply': ['$unitPrice', '$quantity']}}},
            {'$group': {'_id': None, 'totalInventoryValue': {'$sum': '$totalValue'}}}
        ]
        result = list(coll.aggregate(pipeline))
        total_value = result[0]['totalInventoryValue'] if result else 0
        self.query_one("#integrity-total", Static).update(f"Total Inventory Value: ${total_value:,.2f}")

    # Results actions
    def _render_results(self) -> None:
        meta = self.query_one("#results-meta", Static)
        table = self.query_one("#results-table", DataTable)
        items = self.sampled_items
        total_value = sum([i.get('extendedValue', 0) for i in items])
        meta.update(
            f"Collection: {self.selected_collection} | Items: {len(items)} | Total Sampled Value: ${total_value:,.2f}"
        )
        table.clear()
        for it in items:
            table.add_row(
                str(it.get('itemId', 'N/A')),
                str(it.get('description', 'N/A')),
                f"${it.get('unitPrice', 0):,.2f}",
                str(it.get('quantity', 0)),
                f"${it.get('extendedValue', 0):,.2f}",
            )

    def _export_results(self) -> None:
        if not self.sampled_items:
            self.notify("No data to export.")
            return
        filename = f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame([
            {
                'Item ID': i.get('itemId', 'N/A'),
                'Description': i.get('description', 'N/A'),
                'Unit Price': i.get('unitPrice', 0),
                'Quantity': i.get('quantity', 0),
                'Extended Value': i.get('extendedValue', 0),
                'Category': i.get('category', 'N/A'),
                'Supplier': i.get('supplier', 'N/A'),
                'Audit Date': datetime.now().strftime('%Y-%m-%d')
            } for i in self.sampled_items
        ])
        df.to_csv(filename, index=False)
        info = (
            f"✓ Audit results successfully exported to:\n\n"
            f"  {filename}\n\n"
            f"• {len(df)} records exported\n"
            f"• Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• Fields: Item ID, Description, Unit Price, Quantity, Extended Value, Category, Supplier, Audit Date"
        )
        self.query_one("#export-info", Static).update(info)
        self.switch_tab("export")


if __name__ == "__main__":
    AuditApp().run()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd

# Reuse backend from a.py via import
import a as backend


class AuditApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MongoDB Inventory Audit System")
        self.geometry("1000x700")
        self.minsize(900, 600)

        self.db = None
        self.sampled_items = []
        self.selected_collection = None

        self._build_layout()
        self._connect_db()

    def _build_layout(self):
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.frames = {}
        for F in (Dashboard, ConfigScreen, IntegrityScreen, ResultsScreen, ExportScreen):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("Dashboard")

    def _connect_db(self):
        try:
            self.db = backend.connect_to_mongodb()
            self.frames["Dashboard"].update_status(connected=True, db_name=backend.DB_NAME, collections=self.db.list_collection_names())
        except Exception as e:
            self.frames["Dashboard"].update_status(connected=False, db_name="-", collections=[])
            messagebox.showerror("Connection Error", str(e))

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if name == "ConfigScreen":
            frame.refresh_collections()
        if name == "IntegrityScreen":
            frame.refresh_collections()
        if name == "ResultsScreen":
            frame.render_results()


class Dashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        title = ttk.Label(self, text="MONGODB INVENTORY AUDIT SYSTEM", font=("Segoe UI", 18, "bold"))
        title.pack(pady=12)

        self.status = ttk.Label(self, text="Connecting...", font=("Segoe UI", 10))
        self.status.pack(pady=6)

        btns = ttk.Frame(self)
        btns.pack(pady=16)
        ttk.Button(btns, text="Run Audit", command=lambda: controller.show_frame("ConfigScreen")).grid(row=0, column=0, padx=8)
        ttk.Button(btns, text="Data Integrity", command=lambda: controller.show_frame("IntegrityScreen")).grid(row=0, column=1, padx=8)
        ttk.Button(btns, text="Export Data", command=self.go_export).grid(row=0, column=2, padx=8)

    def update_status(self, connected, db_name, collections):
        if connected:
            self.status.config(text=f"✓ Connected to MongoDB | Database: {db_name} | Collections: {len(collections)}")
        else:
            self.status.config(text="✗ Not connected")

    def go_export(self):
        if not self.controller.sampled_items:
            messagebox.showinfo("No Data", "Run an audit first to export results.")
            return
        self.controller.show_frame("ExportScreen")


class ConfigScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.collections = []
        self.counts = {}

        ttk.Label(self, text="CONFIGURE AUDIT PARAMETERS", font=("Segoe UI", 16, "bold")).pack(pady=10)

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=12, pady=6)

        # Collections list
        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left, text="Available Collections:").pack(anchor=tk.W)
        self.tree = ttk.Treeview(left, columns=("count",), show="headings", height=10)
        self.tree.heading("count", text="Items")
        self.tree.column("count", width=120, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=6)

        # Params
        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(right, text="Sample Size (1-500)").pack(anchor=tk.W)
        self.sample_var = tk.IntVar(value=50)
        ttk.Spinbox(right, from_=1, to=500, textvariable=self.sample_var, width=12).pack(pady=4)
        ttk.Label(right, text="Threshold Value ($)").pack(anchor=tk.W, pady=(8, 0))
        self.threshold_var = tk.DoubleVar(value=1000.0)
        ttk.Spinbox(right, from_=0, to=10_000_000, increment=50, textvariable=self.threshold_var, width=12).pack(pady=4)

        # Preview
        self.preview = tk.Text(self, height=6, state=tk.DISABLED)
        self.preview.pack(fill=tk.X, padx=12, pady=6)

        bottom = ttk.Frame(self)
        bottom.pack(pady=8)
        ttk.Button(bottom, text="Cancel", command=lambda: controller.show_frame("Dashboard")).grid(row=0, column=0, padx=8)
        ttk.Button(bottom, text="Run Audit", command=self.run_audit).grid(row=0, column=1, padx=8)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_preview())

    def refresh_collections(self):
        self.tree.delete(*self.tree.get_children())
        self.collections = self.controller.db.list_collection_names() if (self.controller.db is not None) else []
        self.counts = {}
        for name in self.collections:
            try:
                self.counts[name] = self.controller.db[name].count_documents({})
            except Exception:
                self.counts[name] = 0
            self.tree.insert('', tk.END, iid=name, values=(self.counts[name],))
        self.update_preview()

    def update_preview(self):
        sel = self.tree.selection()
        if not sel:
            text = "Select a collection to preview."
        else:
            name = sel[0]
            total = self.counts.get(name, 0)
            sample = self.sample_var.get()
            threshold = self.threshold_var.get()
            pct = (sample / total * 100) if total else 0
            est = int(max(0, round(total * 0.07)))
            text = (
                f"AUDIT PREVIEW:\n"
                f"• Collection: {name}\n"
                f"• Total items: {total:,}\n"
                f"• Sample size: {sample} items ({pct:.1f}% of total)\n"
                f"• Items above ${threshold:,.2f}: ~{est} estimated\n"
            )
        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        self.preview.insert(tk.END, text)
        self.preview.config(state=tk.DISABLED)

    def run_audit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select Collection", "Please select a collection.")
            return
        name = sel[0]
        self.controller.selected_collection = name
        sample_size = max(1, min(500, self.sample_var.get()))
        threshold = max(0.0, float(self.threshold_var.get()))
        coll = self.controller.db[name]
        try:
            sampled_items = backend.perform_price_testing_audit(coll, sample_size, threshold)
        except Exception as e:
            messagebox.showerror("Audit Error", str(e))
            return
        self.controller.sampled_items = sampled_items
        self.controller.show_frame("ResultsScreen")


class IntegrityScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.collections = []

        ttk.Label(self, text="DATA INTEGRITY REPORT", font=("Segoe UI", 16, "bold")).pack(pady=10)
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=12, pady=6)

        self.combo = ttk.Combobox(top, state="readonly")
        self.combo.pack(side=tk.LEFT)
        ttk.Button(top, text="Scan", command=self.scan).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Back", command=lambda: controller.show_frame("Dashboard")).pack(side=tk.LEFT)

        self.table = ttk.Treeview(self, columns=("status", "count", "percent"), show="headings")
        for col, w in (("status", 100), ("count", 100), ("percent", 100)):
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, width=w, anchor=tk.CENTER)
        self.table.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.total_value_label = ttk.Label(self, text="Total Inventory Value: $0.00")
        self.total_value_label.pack(pady=6)

    def refresh_collections(self):
        cols = self.controller.db.list_collection_names() if (self.controller.db is not None) else []
        self.combo['values'] = cols
        if cols:
            self.combo.current(0)

    def scan(self):
        name = self.combo.get()
        if not name:
            messagebox.showinfo("Select Collection", "Please select a collection.")
            return
        coll = self.controller.db[name]
        total_count = coll.count_documents({})
        checks = {
            "Missing ItemID": coll.count_documents({'itemId': {'$exists': False}}),
            "Missing Price": coll.count_documents({'unitPrice': {'$exists': False}}),
            "Missing Quantity": coll.count_documents({'quantity': {'$exists': False}}),
            "Negative Price": coll.count_documents({'unitPrice': {'$lt': 0}}),
            "Negative Qty": coll.count_documents({'quantity': {'$lt': 0}}),
        }
        for row in self.table.get_children():
            self.table.delete(row)
        for label, count in checks.items():
            percent = (count / total_count * 100) if total_count else 0
            status = "PASS" if count == 0 else "WARN"
            self.table.insert('', tk.END, values=(status, count, f"{percent:.1f}%"))
        pipeline = [
            {'$match': {'unitPrice': {'$exists': True}, 'quantity': {'$exists': True}}},
            {'$project': {'totalValue': {'$multiply': ['$unitPrice', '$quantity']}}},
            {'$group': {'_id': None, 'totalInventoryValue': {'$sum': '$totalValue'}}}
        ]
        result = list(coll.aggregate(pipeline))
        total_value = result[0]['totalInventoryValue'] if result else 0
        self.total_value_label.config(text=f"Total Inventory Value: ${total_value:,.2f}")


class ResultsScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="PRICE TESTING AUDIT RESULTS", font=("Segoe UI", 16, "bold")).pack(pady=10)

        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=12)
        self.meta = ttk.Label(top, text="")
        self.meta.pack(side=tk.LEFT)
        ttk.Button(top, text="Refine", command=lambda: controller.show_frame("ConfigScreen")).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Export CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="New Audit", command=lambda: controller.show_frame("ConfigScreen")).pack(side=tk.RIGHT, padx=6)

        cols = ("itemId", "description", "unitPrice", "quantity", "extendedValue")
        self.table = ttk.Treeview(self, columns=cols, show="headings")
        headings = {
            "itemId": "Item ID",
            "description": "Description",
            "unitPrice": "Price",
            "quantity": "Qty",
            "extendedValue": "Value",
        }
        widths = {
            "itemId": 120,
            "description": 420,
            "unitPrice": 120,
            "quantity": 80,
            "extendedValue": 140,
        }
        for c in cols:
            self.table.heading(c, text=headings[c])
            self.table.column(c, width=widths[c], anchor=tk.W if c in ("itemId", "description") else tk.E)
        self.table.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.page_label = ttk.Label(self, text="")
        self.page_label.pack()

    def render_results(self):
        items = self.controller.sampled_items or []
        name = self.controller.selected_collection or "-"
        total_value = sum([i.get('extendedValue', 0) for i in items])
        self.meta.config(text=f"Collection: {name} | Items: {len(items)} | Total Sampled Value: ${total_value:,.2f}")
        for row in self.table.get_children():
            self.table.delete(row)
        for i, item in enumerate(items, 1):
            self.table.insert('', tk.END, values=(
                item.get('itemId', 'N/A'),
                str(item.get('description', 'N/A')),
                f"${item.get('unitPrice', 0):,.2f}",
                item.get('quantity', 0),
                f"${item.get('extendedValue', 0):,.2f}",
            ))
        self.page_label.config(text=f"Showing {len(items)} items")

    def export_csv(self):
        if not self.controller.sampled_items:
            messagebox.showinfo("No Data", "Nothing to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile=f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if not path:
            return
        df = pd.DataFrame([
            {
                'Item ID': i.get('itemId', 'N/A'),
                'Description': i.get('description', 'N/A'),
                'Unit Price': i.get('unitPrice', 0),
                'Quantity': i.get('quantity', 0),
                'Extended Value': i.get('extendedValue', 0),
                'Category': i.get('category', 'N/A'),
                'Supplier': i.get('supplier', 'N/A'),
                'Audit Date': datetime.now().strftime('%Y-%m-%d')
            } for i in self.controller.sampled_items
        ])
        df.to_csv(path, index=False)
        self.controller.frames["ExportScreen"].set_details(path, len(df))
        self.controller.show_frame("ExportScreen")


class ExportScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="EXPORT COMPLETE", font=("Segoe UI", 16, "bold")).pack(pady=10)
        self.info = tk.Text(self, height=10, state=tk.DISABLED)
        self.info.pack(fill=tk.X, padx=12)
        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="Open Folder", command=self.open_folder).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Finish", command=lambda: controller.show_frame("Dashboard")).grid(row=0, column=1, padx=6)
        self._path = None

    def set_details(self, path, records):
        self._path = path
        text = (
            f"✓ Audit results successfully exported to:\n\n"
            f"   {path}\n\n"
            f"File Details:\n"
            f"• {records} records exported\n"
            f"• Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• Fields included: Item ID, Description, Unit Price, Quantity, Extended Value, Category, Supplier, Audit Date\n"
        )
        self.info.config(state=tk.NORMAL)
        self.info.delete("1.0", tk.END)
        self.info.insert(tk.END, text)
        self.info.config(state=tk.DISABLED)

    def open_folder(self):
        if not self._path:
            return
        import os
        folder = os.path.dirname(self._path)
        try:
            os.startfile(folder)
        except Exception:
            messagebox.showinfo("Open Folder", folder)


if __name__ == "__main__":
    app = AuditApp()
    app.mainloop()


