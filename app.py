import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Apni Dukan", 
    page_icon="🌿", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# --- 2. CSS FOR VISIBILITY ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    label, p, .stMarkdown {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stSidebar"] { background-color: #2e5a27 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3 { color: #2e5a27 !important; text-align: center; }
    .stButton>button {
        background-color: #e67e22 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 4. CUSTOM DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]

# Generate Flat Numbers as per your specific logic
FLATS = ["001", "002", "003", "004"]  # Ground Floor
for floor in range(1, 19):            # Floors 1 to 18
    for flat in range(1, 5):          # 4 flats per floor
        FLATS.append(f"{floor}{flat:02d}")

# --- 5. NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

if st.sidebar.button("🏠 Back to Home"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- SECTION: HOME DASHBOARD ---
if st.session_state.page == "🏠 Home":
    st.title("🌿 Apni Dukan")
    st.subheader("Select a Task")
    
    if st.button("📦 Inventory Manager"):
        st.session_state.page = "📦 Inventory Manager"; st.rerun()
    if st.button("📢 Marketing"):
        st.session_state.page = "📢 Marketing"; st.rerun()
    if st.button("📝 Billing"):
        st.session_state.page = "📝 Billing"; st.rerun()
    if st.button("📊 Daily Reports"):
        st.session_state.page = "📊 Daily Reports"; st.rerun()

# --- SECTION: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.header("📝 Create New Bill")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            name = st.text_input("Customer Name")
            tow = st.selectbox("Select Tower", TOWERS)
            flt = st.selectbox("Select Flat No", FLATS)
            itm = st.selectbox("Select Item", df_inv["name"].tolist())
            unt = st.selectbox("Select Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Enter Quantity", min_value=0.1)
            
            if st.form_submit_button("Generate Bill"):
                row = df_inv[df_inv["name"] == itm].iloc[0]
                c_qty = qty/1000 if unt == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                prof = round((row["sale_price"] - row["cost_price"]) * c_qty, 2)
                
                db.table("sales").insert({
                    "item_name": itm, "qty": f"{qty} {unt}", 
                    "total_bill": tot, "profit": prof, 
                    "tower_flat": f"T-{tow} {flt}"
                }).execute()
                
                msg = f"*Apni Dukan Receipt*\n*Cust:* {name}\n*Loc:* T-{tow} {flt}\n*Item:* {itm}\n*Qty:* {qty}{unt}\n*Total: ₹{tot}*"
                st.link_button("📲 Send WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
    else:
        st.info("Inventory empty. Please add items first.")

# --- OTHER SECTIONS (Inventory, Marketing, Reports) ---
# (The logic for these remains the same as our previous working version)
elif st.session_state.page == "📦 Inventory Manager":
    st.header("📦 Inventory Manager")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    # ... Inventory code ...

elif st.session_state.page == "📢 Marketing":
    st.header("📢 Marketing")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    # ... Marketing code ...

elif st.session_state.page == "📊 Daily Reports":
    st.header("📊 Daily Reports")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    # ... Reports code ...
