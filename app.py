import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & THEME ---
# initial_sidebar_state="expanded" ensures the sidebar stays open
st.set_page_config(
    page_title="Apni Dukan Manager", 
    page_icon="🌿", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS for Colors and Styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f9fbf9;
    }
    [data-testid="stSidebar"] {
        background-color: #2e5a27;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .st-emotion-cache-10trblm {
        color: #2e5a27;
    }
    h1, h2, h3 {
        color: #2e5a27 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #e67e22 !important;
        color: white !important;
        border-radius: 8px;
        border: none;
    }
    </style>
    """, unsafe_content_factory=True)

# --- 2. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 3. DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = [f"{floor}{flat:02d}" for floor in range(1, 19) for flat in range(1, 5)]

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.image("https://img.icons8.com/color/96/shop-local.png")
st.sidebar.title("Apni Dukan")
menu = ["📦 Inventory Manager", "📢 Marketing", "📝 Billing", "📊 Daily Reports"]
choice = st.sidebar.radio("Main Menu", menu)

# --- SECTION 1: INVENTORY MANAGER ---
if choice == "📦 Inventory Manager":
    st.header("📦 Inventory & Price Management")
    
    # NEW: Add custom items to the Master List
    with st.expander("⚙️ Master List Settings (Add new items to dropdown)"):
        new_master_item = st.text_input("New Item Name (e.g. Avocado)")
        if st.button("Add to Dropdown List"):
            if new_master_item:
                # We store master items in a separate table for persistence
                db.table("master_list").upsert({"name": new_master_item}).execute()
                st.success(f"{new_master_item} added to Master List!")
                st.rerun()

    # Load items from Master List table
    master_res = db.table("master_list").select("*").execute()
    master_list = sorted([item['name'] for item in master_res.data]) if master_res.data else ["Potato (Aloo)", "Onion (Pyaz)"]

    with st.container(border=True):
        st.subheader("➕ Update Shop Stock")
        with st.form("add_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                p_name = st.selectbox("Select Product", master_list)
            with col2:
                c_price = st.number_input("Cost (Buy)", min_value=0.0)
            with col3:
                s_price = st.number_input("Sale (Sell)", min_value=0.0)
            
            is_flash = st.checkbox("Mark for Flash Sale")
            if st.form_submit_button("Update Inventory"):
                db.table("inventory").upsert({
                    "name": p_name, "cost_price": c_price, 
                    "sale_price": s_price, "is_flash_sale": is_flash
                }).execute()
                st.success(f"{p_name} updated!")
                st.rerun()

    # Table View
    st.subheader("📋 Current Prices")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.data_editor(df, num_rows="dynamic", key="inv_edit", hide_index=True)

# --- SECTION 2: MARKETING ---
elif choice == "📢 Marketing":
    st.header("📢 WhatsApp Marketing")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        
        tab1, tab2 = st.tabs(["Daily Price List", "Flash Sale"])
        
        with tab1:
            st.write("Generate a full price list for your society group.")
            if st.button("Generate Daily List"):
                msg = f"*🏪 Apni Dukan - Fresh Arrivals ({datetime.now().strftime('%d %b')})*\n\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                msg += "\n📍 Home Delivery Available!\n📞 Order Now!"
                st.link_button("🚀 Share to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        
        with tab2:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("Generate Flash Sale Blast"):
                    msg = "⚡ *FLASH SALE - APNI DUKAN* ⚡\n\n"
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}* only!\n"
                    msg += "\n⏳ Valid for 2 hours!"
                    st.link_button("🚀 Send Flash Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")
            else:
                st.info("No items marked for Flash Sale in Inventory.")

# --- SECTION 3: BILLING ---
elif choice == "📝 Billing":
    st.header("📝 New Bill")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            c_name = st.text_input("Customer Name")
            c1, c2 = st.columns(2)
            with c1:
                tower = st.selectbox("Tower", TOWERS)
                flat = st.selectbox("Flat No", FLATS)
            with c2:
                item = st.selectbox("Item", df_inv["name"].tolist())
                unit = st.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
                qty = st.number_input("Quantity", min_value=0.1, step=0.1)
            
            if st.form_submit_button("Generate & Share"):
                item_row = df_inv[df_inv["name"] == item].iloc[0]
                # Adjust total if unit is gms
                calc_qty = qty/1000 if unit == "gms" else qty
                total = item_row["sale_price"] * calc_qty
                profit = (item_row["sale_price"] - item_row["cost_price"]) * calc_qty
                
                db.table("sales").insert({
                    "item_name": item, "qty": f"{qty} {unit}", 
                    "total_bill": round(total, 2), "profit": round(profit, 2), 
                    "tower_flat": f"Tower {tower}-{flat}"
                }).execute()
                
                msg = f"*Apni Dukan Receipt*\n*Cust:* {c_name}\n*Loc:* Tower {tower}-{flat}\n*Item:* {item} ({qty} {unit})\n*Total: ₹{round(total, 2)}*"
                st.link_button("📲 Share on WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
    else:
        st.error("Inventory empty!")

# --- SECTION 4: REPORTS ---
elif choice == "📊 Daily Reports":
    st.header("📊 Business Insights")
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        c1, c2 = st.columns(2)
        c1.metric("Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        c2.metric("Profit", f"₹{sdf['profit'].sum():.2f}")
        st.dataframe(sdf, use_container_width=True)
    else:
        st.info("No sales data yet.")
