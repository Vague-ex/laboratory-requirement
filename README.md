# Audit App – Multi-GUI Price Testing & Inventory Audits

A Python tool to help you check inventory prices and run audits, with a choice of classic or modern GUIs.

---

## What This Does
- **Price Testing Audit (Problem Set 5)** – already working and tested.
- **Multiple GUIs**:  
  - **Tkinter**: the simple one that works right now.  
  - **Qt**: a more modern look, still a work in progress.
- Scripts can run on their own or inside the GUIs.

---

## Connecting to MongoDB (with mongopy)
We use **mongopy** (a small wrapper around pymongo) to talk to MongoDB.

1. Install what you need:
   ```bash
   pip install mongopy pymongo
   ```
2. Put your connection string in a `.env` file or pass it when starting:
   ```
   MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority
   ```
3. Quick example:
   ```python
   from mongopy import MongoClient

   client = MongoClient(MONGO_URI)
   db = client["InventoryDB"]
   collection = db["Items"]
   items = list(collection.find({"category": "Hardware"}))
   ```

The Tkinter app will ask for this URI the first time you run it. You can change it later in Settings.

---

## Price Testing Audit (Problem Set 5)
Checks if an item’s **unit price** jumped higher than allowed.

Steps:
1. Grab these fields from MongoDB: `ItemID`, `Description`, `UnitPrice`, `Quantity`, `ExtendedValue`, `Category`, `Supplier`.
2. Compare current unit prices with a baseline or older data.
3. Flag anything over the set increase.

Run it by itself:
```bash
python price_test_audit.py --mongo-uri "your_uri"
```
It will print results or save to JSON/CSV.

---

## Current Status
| Part                  | Status        | Notes                                 |
|-----------------------|--------------|---------------------------------------|
| Tkinter GUI           | ✅ Working   | Lets you pick audits and connect DB.  |
| Price Test Audit      | ✅ Working   | Runs standalone or with Tkinter GUI.  |
| Other Audit Scripts   | 🚧 Not done  | Placeholders for now.                 |
| Qt GUI                | 🚧 WIP       | Modern style, still unfinished.       |

---

## Run It
Tkinter GUI:
```bash
python audit_gui_tkinter.py
```

Qt GUI (prototype):
```bash
python audit_gui_qt.py
```

---

## Folder Peek
```
.
├─ audit_gui_tkinter.py   # classic GUI
├─ audit_gui_qt.py        # modern GUI (WIP)
├─ price_test_audit.py    # problem set 5 audit
├─ other_audit_scripts/   # future audits
├─ utils/                 # helpers for db, config
└─ README.md              # this file
```

---

## To‑Do Next
- Finish the Qt GUI for a slicker interface.
- Add more audits.
- Export results to Excel or PDF.
- Optional login/auth.

---

Tip: Make sure your MongoDB cluster allows your IP and you’re on Python 3.10 or newer.
