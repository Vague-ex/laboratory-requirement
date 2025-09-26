import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
from PriceTestAuditScript import (
    perform_price_testing_audit,
    export_audit_results,
    find_low_stock_items,
    find_high_unit_price_items
)

class AuditApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Audit Dashboard")
        self.setMinimumSize(1000, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Inventory Audit Dashboard")
        title.setStyleSheet("font-size: 28px; color: #0d6efd; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Controls
        controls = QHBoxLayout()
        self.audit_type = QComboBox()
        self.audit_type.addItems(["Price Testing", "Low Stock", "High Unit Price"])
        controls.addWidget(QLabel("Audit Type:"))
        controls.addWidget(self.audit_type)

        self.sample_size = QLineEdit("3")
        self.sample_size.setFixedWidth(60)
        controls.addWidget(QLabel("Sample Size:"))
        controls.addWidget(self.sample_size)

        self.threshold = QLineEdit("5000")
        self.threshold.setFixedWidth(80)
        controls.addWidget(QLabel("Threshold Value:"))
        controls.addWidget(self.threshold)

        self.run_btn = QPushButton("Run Audit")
        self.run_btn.clicked.connect(self.run_audit)
        controls.addWidget(self.run_btn)

        layout.addLayout(controls)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Item ID', 'Description', 'Unit Price', 'Quantity', 'Extended Value',
            'Category', 'Supplier', 'Audit Date'
        ])
        self.table.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.table)

        # Status
        self.status = QLabel("Ready.")
        self.status.setStyleSheet("background: #e9ecef; padding: 6px; font-size: 13px;")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def run_audit(self):
        try:
            audit_type = self.audit_type.currentText()
            sample_size = int(self.sample_size.text())
            threshold_value = float(self.threshold.text())
            if audit_type == "Price Testing":
                sampled_items = perform_price_testing_audit(sample_size, threshold_value)
                df = export_audit_results(sampled_items, filename=None)
                self.status.setText(f"Sampled {len(sampled_items)} items above ${threshold_value}")
            elif audit_type == "Low Stock":
                low_stock_items = find_low_stock_items(stock_threshold=int(self.threshold.text()))
                df = export_audit_results(low_stock_items, filename=None)
                self.status.setText(f"Found {len(low_stock_items)} items below stock {self.threshold.text()}")
            elif audit_type == "High Unit Price":
                high_price_items = find_high_unit_price_items(unit_price_threshold=threshold_value)
                df = export_audit_results(high_price_items, filename=None)
                self.status.setText(f"Found {len(high_price_items)} items above unit price ${self.threshold.text()}")
            else:
                self.status.setText("Unknown audit type.")
                return
            self.populate_table(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.status.setText("Error running audit.")

    def populate_table(self, df):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(df.to_dict(orient='records')):
            self.table.insertRow(row_idx)
            for col_idx, key in enumerate([
                'Item ID', 'Description', 'Unit Price', 'Quantity', 'Extended Value',
                'Category', 'Supplier', 'Audit Date'
            ]):
                value = str(item.get(key, ""))
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuditApp()
    window.show()
    sys.exit(app.exec_())
