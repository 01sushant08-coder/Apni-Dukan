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

st.markdown("""
    <style>
    .stApp { background-color: #f9fbf9; }
    [data-testid="stSidebar"] { background-color: #2e5a27 !important; }
    .main-btn {
        background-color: #e67e22 !important;
        color: white !important;
        padding: 20px;
        text-align: center;
        border-radius: 10px;
        margin: 10px 0px;
        font-weight: bold;
        cursor: pointer;
    }
    h1, h2 { color: #2e5a27 !important; text-align: center; }
    /* Force focus to main area */
    section[data-testid="stSidebar"] { width: 0px; } 
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 3. DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = [f"{floor}{flat:02d}" for floor in range(1, 19) for flat in range(1, 5)]

# --- 4. NAVIGATION LOGIC ---
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

# Persistent Home Button in Sidebar
if st.sidebar.button("🏠 Back to Home"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- SECTION: HOME DASHBOARD ---
if st.session_state.page == "🏠 Home":
    st.title("🌿 Apni Dukan")
    st.subheader("Select a Task")
    
    col1, col2 = st.columns(2)
    
    if col1.button("📦 Inventory Manager", use_container_width=True):
        st.session_state.page = "📦 Inventory Manager"
        st.rerun()
        
    if col2.button("📢 Marketing", use_container_width=True):
        st.session_state.page = "📢 Marketing"
        st.rerun()
        
    if col1.button("📝 Billing", use_container_width=True):
        st.session_state.page = "📝 Billing"
        st.rerun()
        
    if col2.button("📊 Daily Reports", use_container_width=True):
        st.session_state.page = "📊 Daily Reports"
        st.rerun()

# --- SECTION 1: INVENTORY MANAGER ---
elif st.session_state.page == "📦 Inventory Manager":
    st.header("📦 Inventory Manager")
    if st.button("⬅️ Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.expander("⚙️ Master List Settings"):
        new_master_item = st.text_input("New Item Name")
        if st.button("Add to Master"):
            if new_master_item:
                db.table("master_list").upsert({"name": new_master_item}).execute()
                st.success("Added!")
                st.rerun()

    try:
        master_res = db.table("master_list").select("*").execute()
        master_options = sorted([item['name'] for item in master_res.data]) if master_res.data else ["Potato"]
    except:
        master_options = ["Potato"]

    with st.form("add_form", clear_on_submit=True):
        p_name = st.selectbox("Product", master_options)
        c_price = st.number_input("Cost/kg", min_value=0.0)
        s_price = st.number_input("Sale/kg", min_value=0.0)
        is_flash = st.checkbox("Flash Sale?")
        if st.form_submit_button("Update Inventory"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_price, "sale_price": s_price, "is_flash_sale": is_flash}).execute()
            st.success("Updated!")

# --- SECTION 2: MARKETING ---
elif st.session_state.page == "📢 Marketing":
    st.header("📢 Marketing")
    if st.button("⬅️ Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        m_type = st.radio("Message Type", ["Daily List", "Flash Sale"], horizontal=True)
        
        if m_type == "Daily List":
            if st.button("Generate Daily Price List"):
                msg = f"*🏪 Apni Dukan - Fresh Arrivals*\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                st.link_button("🚀 Share to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("Generate Flash Blast"):
                    msg = "⚡ *FLASH SALE* ⚡\n"
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}*!\n"
                    st.link_button("🚀 Send Flash Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION 3: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.header("📝 New Bill")
    if st.button("⬅️ Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            c_name = st.text_input("Customer Name")
            tower = st.selectbox("Tower", TOWERS)
            flat = st.selectbox("Flat", FLATS)
            item = st.selectbox("Item", df_inv["name"].tolist())
            unit = st.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Quantity", min_value=0.1)
            
            if st.form_submit_button("Generate Bill"):
                item_row = df_inv[df_inv["name"] == item].iloc[0]
                calc_qty = qty/1000 if unit == "gms" else qty
                total = round(item_row["sale_price"] * calc_qty, 2)
                profit = round((item_row["sale_price"] - item_row["cost_price"]) * calc_qty, 2)
                
                db.table("sales").insert({"item_name": item, "qty": f"{qty} {unit}", "total_bill": total, "profit": profit, "tower_flat": f"T-{tower} {flat}"}).execute()
                
                msg = f"*Apni Dukan Receipt*\n*Cust:* {c_name}\n*Loc:* T-{tower} {flat}\n*Item:* {item}\n*Qty:* {qty}{unit}\n*Total: ₹{total}*"
                st.link_button("📲 Share Bill", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION 4: REPORTS ---
elif st.session_state.page == "📊 Daily Reports":
    st.header("📊 Daily Reports")
    if st.button("⬅️ Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        st.metric("Total Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        st.metric("Total Profit", f"₹{sdf['profit'].sum():.2f}")
        st.dataframe(sdf, use_container_width=True)
