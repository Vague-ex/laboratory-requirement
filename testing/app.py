import streamlit as st
from db import MongoDBConnection
import audit

conn = MongoDBConnection()

st.set_page_config(page_title="Inventory Audit", layout="wide")

st.title("📦 Inventory Audit Application")

# Session state for DB
if "db_uri" not in st.session_state:
    st.session_state.db_uri = ""
if "db_name" not in st.session_state:
    st.session_state.db_name = ""
if "collection" not in st.session_state:
    st.session_state.collection = None

# Sidebar navigation
menu = st.sidebar.radio("Menu", ["Connect", "Audit Functions", "Settings"])

if menu == "Connect":
    st.subheader("🔗 Connect to MongoDB")
    uri = st.text_input("MongoDB URI", st.session_state.db_uri or "mongodb+srv://...")
    db_name = st.text_input("Database Name", st.session_state.db_name or "inventoryaudit")

    if st.button("Connect"):
        try:
            db = conn.connect(uri, db_name)
            st.session_state.db_uri = uri
            st.session_state.db_name = db_name
            st.success("Connected successfully!")
            collections = conn.get_collections()
            choice = st.selectbox("Pick Collection", collections)
            if choice:
                st.session_state.collection = db[choice]
        except Exception as e:
            st.error(f"Connection failed: {e}")

elif menu == "Audit Functions":
    if not st.session_state.collection:
        st.warning("Please connect to MongoDB first.")
    else:
        col = st.session_state.collection
        st.subheader("📝 Audit Checks")

        func = st.selectbox("Choose Audit Function", [
            "Cost Increase",
            "Obsolete Inventory",
            "Sample Tags",
            "Missing/Duplicate Tags",
            "Random Price Sample",
            "Net Realizable Value Test"
        ])

        if func == "Cost Increase":
            last_year = st.text_input("Last Year Field", "2022")
            this_year = st.text_input("This Year Field", "2023")
            min_cost = st.number_input("Minimum Cost", 0.0)
            pct_increase = st.number_input("Percentage Increase", 10.0)
            if st.button("Run Audit"):
                result = audit.cost_increase(col, last_year, this_year, min_cost, pct_increase)
                st.write(result)

        elif func == "Obsolete Inventory":
            threshold = st.number_input("Threshold Quantity", 50)
            cutoff = st.date_input("Cutoff Date")
            if st.button("Run Audit"):
                result = audit.obsolete_inventory(col, threshold, cutoff.isoformat())
                st.write(result)

        elif func == "Sample Tags":
            size = st.slider("Sample Size", 1, 20, 5)
            if st.button("Run Audit"):
                result = audit.sample_tags(col, size)
                st.write(result)

        elif func == "Missing/Duplicate Tags":
            tag_field = st.text_input("Tag Field", "tag_number")
            if st.button("Run Audit"):
                result = audit.missing_or_duplicate_tags(col, tag_field)
                st.write(result)

        elif func == "Random Price Sample":
            min_value = st.number_input("Min Extended Value", 100.0)
            size = st.slider("Sample Size", 1, 20, 5)
            if st.button("Run Audit"):
                result = audit.random_price_sample(col, min_value, size)
                st.write(result)

        elif func == "Net Realizable Value Test":
            if st.button("Run Audit"):
                result = audit.nrv_test(col)
                st.write(result)

elif menu == "Settings":
    st.subheader("⚙️ Settings")
    if st.button("Reset Connection"):
        st.session_state.db_uri = ""
        st.session_state.db_name = ""
        st.session_state.collection = None
        st.success("Connection reset")
