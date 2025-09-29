import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QProgressBar,
    QDialog, QListWidget, QListWidgetItem, QCheckBox, QDialogButtonBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from PriceTestAuditScript import (
    perform_price_testing_audit,
    export_audit_results,
    find_low_stock_items,
    find_high_unit_price_items,
    get_collection_names,
    audit_all_collections,
    db
)
from OtherAuditScripts import (
    merge_and_list_increased_items,
    list_excess_inventory_and_obsolete,
    scan_tag_sequence
)   

class CollectionSelectorDialog(QDialog):
    def __init__(self, collection_names, selected=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Collections to Audit")
        self.resize(350, 400)
        self.selected = selected if selected is not None else collection_names
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for name in collection_names:
            item = QListWidgetItem(name)
            item.setSelected(name in self.selected)
            self.list_widget.addItem(item)
        layout.addWidget(QLabel("Select collections to audit:"))
        layout.addWidget(self.list_widget)
        self.all_checkbox = QCheckBox("Audit ALL collections")
        self.all_checkbox.setChecked(len(self.selected) == len(collection_names))
        self.all_checkbox.stateChanged.connect(self.toggle_all)
        layout.addWidget(self.all_checkbox)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def toggle_all(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setSelected(state == 2)

    def get_selected_collections(self):
        if self.all_checkbox.isChecked():
            return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        return [item.text() for item in self.list_widget.selectedItems()]

class AuditApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Dashboard")
        self.setMinimumSize(1000, 600)
        self.selected_collections = get_collection_names()  # Default: all
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Inventory Dashboard")
        title.setStyleSheet("font-size: 28px; color: #0d6efd; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Controls
        controls = QHBoxLayout()
        self.audit_type = QComboBox()
        self.audit_type.addItems(["Price Testing", "Low Stock", "High Unit Price", "Merge and List", "Excess items", "Scan tags"])
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

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        controls.addWidget(self.settings_btn)

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

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Status
        self.status = QLabel("Ready.")
        self.status.setStyleSheet("background: #e9ecef; padding: 6px; font-size: 13px;")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def open_settings(self):
        dialog = CollectionSelectorDialog(get_collection_names(), self.selected_collections, self)
        if dialog.exec_():
            self.selected_collections = dialog.get_selected_collections()
            if len(self.selected_collections) == len(get_collection_names()):
                self.status.setText("Audit will run on ALL collections.")
            else:
                self.status.setText(f"Audit will run on: {', '.join(self.selected_collections)}")

    def run_audit(self):
        try:
            audit_type = self.audit_type.currentText()
            sample_size = int(self.sample_size.text())
            threshold_value = float(self.threshold.text())
            self.progress.setValue(0)
            collection_names = self.selected_collections
            all_results = {}
            total = len(collection_names)
            for idx, col_name in enumerate(collection_names, 1):
                self.progress.setValue(int(idx / total * 100))
                collection = db[col_name]
                if audit_type == "Price Testing":
                    items = perform_price_testing_audit(collection, sample_size, threshold_value)
                elif audit_type == "Low Stock":
                    items = find_low_stock_items(collection, stock_threshold=int(self.threshold.text()))
                elif audit_type == "High Unit Price":
                    items = find_high_unit_price_items(collection, unit_price_threshold=threshold_value)
                elif audit_type == "Merge and List":
                    items = merge_and_list_increased_items(collection, sample_size, threshold_value)
                elif audit_type == "Excess items":
                    items = list_excess_inventory_and_obsolete(collection, sample_size, threshold_value)
                elif audit_type == "Scan tags":
                    items = scan_tag_sequence(collection)
                else:
                    items = []
                all_results[col_name] = items
            self.progress.setValue(100)
            # Combine all results for display
            combined = []
            for col, items in all_results.items():
                for item in items:
                    item['Collection'] = col
                    combined.append(item)
            if combined:
                df = export_audit_results(combined, filename=None)
                self.status.setText(f"Audited {len(combined)} items across {len(collection_names)} collections.")
                self.populate_table(df)
            else:
                self.status.setText("No items found for audit.")
                self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.status.setText("Error running audit.")
            self.progress.setValue(0)

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
            # Optionally show collection name in status or add column

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome")
        self.setFixedSize(400, 400)  # Increased height for larger image
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)  # Center all widgets vertically
        label = QLabel("Inventory Audit Program")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 22px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(label)
        author = QLabel("Created by Vague-Ex")
        author.setAlignment(Qt.AlignCenter)
        author.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(author)
        
        pic = QLabel()
        pic.setFixedSize(240, 240)  # 100% larger than previous 120x120
        pic.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("vague.jpg")
        if pixmap.isNull():
            pixmap = QPixmap(240, 240)
            pixmap.fill(Qt.lightGray)
        else:
            pixmap = pixmap.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pic.setPixmap(pixmap)
        layout.addWidget(pic, alignment=Qt.AlignCenter)  # Explicitly center the image
        self.setLayout(layout)

def show_main():
    global main_window  # Prevent garbage collection
    main_window = AuditApp()
    main_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    QTimer.singleShot(2000, splash.close)
    QTimer.singleShot(2000, show_main) 
    sys.exit(app.exec_())
    sys.exit(app.exec_())
