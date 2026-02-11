import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & THEME ---
st.set_page_config(
    page_title="Apni Dukan Manager", 
    page_icon="🌿", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #f9fbf9; }
    [data-testid="stSidebar"] { background-color: #2e5a27 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3 { color: #2e5a27 !important; }
    .stButton>button { background-color: #e67e22 !important; color: white !important; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 3. DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = [f"{floor}{flat:02d}" for floor in range(1, 19) for flat in range(1, 5)]

# --- 4. SIDEBAR ---
st.sidebar.title("🌿 Apni Dukan")
menu = ["📦 Inventory Manager", "📢 Marketing", "📝 Billing", "📊 Daily Reports"]
choice = st.sidebar.radio("Main Menu", menu)

# --- SECTION 1: INVENTORY MANAGER ---
if choice == "📦 Inventory Manager":
    st.header("📦 Inventory & Price Management")
    
    with st.expander("⚙️ Master List Settings (Add items to dropdown)"):
        new_master_item = st.text_input("New Item Name")
        if st.button("Add to Master List"):
            if new_master_item:
                db.table("master_list").upsert({"name": new_master_item}).execute()
                st.success(f"{new_master_item} added!")
                st.rerun()

    try:
        master_res = db.table("master_list").select("*").execute()
        master_options = sorted([item['name'] for item in master_res.data]) if master_res.data else ["Potato (Aloo)"]
    except:
        master_options = ["Potato (Aloo)", "Onion (Pyaz)"]

    with st.container(border=True):
        st.subheader("➕ Update Shop Stock")
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            p_name = c1.selectbox("Product", master_options)
            c_price = c2.number_input("Cost Price/kg", min_value=0.0)
            s_price = c3.number_input("Sale Price/kg", min_value=0.0)
            is_flash = st.checkbox("Flash Sale?")
            if st.form_submit_button("Update Inventory"):
                db.table("inventory").upsert({
                    "name": p_name, "cost_price": c_price, 
                    "sale_price": s_price, "is_flash_sale": is_flash
                }).execute()
                st.rerun()

    res = db.table("inventory").select("*").execute()
    if res.data:
        st.subheader("📋 Current Prices")
        st.data_editor(pd.DataFrame(res.data), num_rows="dynamic", key="inv_edit", hide_index=True)

# --- SECTION 2: MARKETING ---
elif choice == "📢 Marketing":
    st.header("📢 WhatsApp Marketing")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        t1, t2 = st.tabs(["Daily List", "Flash Sale"])
        with t1:
            if st.button("Generate Daily List"):
                msg = f"*🏪 Apni Dukan - Fresh Arrivals*\n\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                st.link_button("🚀 Share to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        with t2:
            flash_df = df[df["is_flash_sale"] == True]
            if st.button("Generate Flash Blast") and not flash_df.empty:
                msg = "⚡ *FLASH SALE* ⚡\n\n"
                for _, row in flash_df.iterrows():
                    msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}*!\n"
                st.link_button("🚀 Send Flash Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION 3: BILLING ---
elif choice == "📝 Billing":
    st.header("📝 New Bill")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            c_name = st.text_input("Customer Name")
            c1, c2 = st.columns(2)
            tower = c1.selectbox("Tower", TOWERS)
            flat = c1.selectbox("Flat", FLATS)
            item = c2.selectbox("Item", df_inv["name"].tolist())
            unit = c2.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = c2.number_input("Quantity", min_value=0.1)
            
            if st.form_submit_button("Generate Bill"):
                item_row = df_inv[df_inv["name"] == item].iloc[0]
                calc_qty = qty/1000 if unit == "gms" else qty
                total = round(item_row["sale_price"] * calc_qty, 2)
                profit = round((item_row["sale_price"] - item_row["cost_price"]) * calc_qty, 2)
                
                db.table("sales").insert({
                    "item_name": item, "qty": f"{qty} {unit}", 
                    "total_bill": total, "profit": profit, 
                    "tower_flat": f"T-{tower} {flat}"
                }).execute()
                
                msg = f"*Apni Dukan Receipt*\n*Cust:* {c_name}\n*Loc:* T-{tower} {flat}\n*Item:* {item}\n*Qty:* {qty}{unit}\n*Total: ₹{total}*"
                st.link_button("📲 Share Bill", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION 4: REPORTS ---
elif choice == "📊 Daily Reports":
    st.header("📊 Business Insights")
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        st.metric("Total Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        st.metric("Total Profit", f"₹{sdf['profit'].sum():.2f}")
        st.dataframe(sdf, use_container_width=True)
