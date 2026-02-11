import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & SECRETS ---
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎")

URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]

@st.cache_resource
def get_db():
    return create_client(URL, KEY)

db = get_db()

# --- 2. MASTER PRODUCT LIST (The Dropdown Options) ---
# This ensures he doesn't have to type. He just picks from here.
MASTER_PRODUCTS = sorted([
    "Potato (Aloo)", "Onion (Pyaz)", "Tomato (Tamatar)", "Ginger (Adrak)", "Garlic (Lahsun)",
    "Green Chilli", "Lemon", "Coriander", "Mint (Pudina)", "Spinach (Palak)", 
    "Cauliflower", "Cabbage", "Lady Finger (Bhindi)", "Brinjal (Long)", "Brinjal (Round)",
    "Bottle Gourd (Lauki)", "Bitter Gourd (Karela)", "Ridge Gourd (Tori)", "Pumpkin",
    "Capsicum (Green)", "Capsicum (Red/Yellow)", "Carrot", "Radish (Mooli)", "Cucumber",
    "French Beans", "Cluster Beans (Gawar)", "Green Peas (Matar)", "Broccoli", "Mushroom",
    "Sweet Potato", "Beetroot", "Drumstick", "Colocasia (Arbi)", "Pointed Gourd (Parwal)",
    "Banana (Raw)", "Apple (Royal)", "Apple (Shimla)", "Banana (Kela)", "Papaya",
    "Pomegranate (Anar)", "Guava", "Orange", "Kinnow", "Grapes (Green)", "Grapes (Black)",
    "Watermelon", "Muskmelon", "Mango (Safeda)", "Mango (Dashari)", "Mango (Langra)",
    "Pineapple", "Chickoo", "Pear", "Kiwi", "Dragon Fruit", "Coconut Water", "Litchi",
    "Strawberry", "Custard Apple", "Plum", "Peach", "Apricot"
])

# --- 3. UI ---
st.title("🏪 Apni Dukan")
menu = ["Billing & WhatsApp", "Inventory Manager", "Daily Reports"]
choice = st.sidebar.selectbox("Menu", menu)

# --- INVENTORY MANAGER (With Dropdown) ---
if choice == "Inventory Manager":
    st.header("📦 Manage Shop Stock")
    
    # Form to add from Master List
    with st.expander("➕ Add Item to Shop"):
        with st.form("add_form", clear_on_submit=True):
            # DROPDOWN FOR PRODUCT NAME
            p_name = st.selectbox("Select Product", MASTER_PRODUCTS)
            c_price = st.number_input("Cost Price (Buy)", min_value=0.0)
            s_price = st.number_input("Sale Price (Sell)", min_value=0.0)
            
            if st.form_submit_button("Add to My Shop"):
                db.table("inventory").upsert({
                    "name": p_name, "cost_price": c_price, "sale_price": s_price
                }).execute()
                st.success(f"Updated {p_name} in your inventory!")
                st.rerun()

    # View and Delete current items
    st.subheader("Current Shop Prices")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        # Editor allows quick price updates
        edited = st.data_editor(df, num_rows="dynamic", key="main_inv", hide_index=True)
        if st.button("💾 Save All Price Updates"):
            for _, row in edited.iterrows():
                db.table("inventory").upsert({
                    "id": row["id"], "name": row["name"], 
                    "cost_price": row["cost_price"], "sale_price": row["sale_price"]
                }).execute()
            st.success("Prices Updated!")
    else:
        st.info("Your shop is empty. Add items using the form above.")

# --- BILLING & WHATSAPP ---
elif choice == "Billing & WhatsApp":
    st.header("📝 Create Bill")
    inv = db.table("inventory").select("*").execute()
    if inv.data:
        df_inv = pd.DataFrame(inv.data)
        with st.form("bill_form"):
            c_name = st.text_input("Customer Name")
            flat = st.text_input("Tower/Flat")
            # Dropdown only shows items your friend has added to his shop
            item_choice = st.selectbox("Select Item", df_inv["name"].tolist())
            qty = st.number_input("Quantity", min_value=0.1)
            
            if st.form_submit_button("Share Bill"):
                item_row = df_inv[df_inv["name"] == item_choice].iloc[0]
                total = item_row["sale_price"] * qty
                profit = (item_row["sale_price"] - item_row["cost_price"]) * qty
                
                db.table("sales").insert({
                    "item_name": item_choice, "qty": qty, 
                    "total_bill": total, "profit": profit, "tower_flat": flat
                }).execute()
                
                msg = f"*Apni Dukan Receipt*\nItem: {item_choice}\nQty: {qty}\nTotal: ₹{total}"
                st.link_button("📲 Send WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
    else:
        st.error("No items in shop! Go to Inventory Manager.")

# --- REPORTS ---
elif choice == "Daily Reports":
    st.header("📊 Sales Report")
    sales = db.table("sales").select("*").execute()
    if sales.data:
        sdf = pd.DataFrame(sales.data)
        st.metric("Total Profit", f"₹{sdf['profit'].sum()}")
        st.dataframe(sdf[["created_at", "item_name", "total_bill", "tower_flat"]], use_container_width=True)
# --- Updated Billing Save Logic ---
if st.form_submit_button("Share Bill"):
    try:
        item_row = df_inv[df_inv["name"] == item_choice].iloc[0]
        total = item_row["sale_price"] * qty
        profit = (item_row["sale_price"] - item_row["cost_price"]) * qty
        
        # This is the part that was failing
        db.table("sales").insert({
            "item_name": item_choice, 
            "qty": qty, 
            "total_bill": total, 
            "profit": profit, 
            "tower_flat": flat
        }).execute()
        
        # If successful, show WhatsApp link
        msg = f"*Apni Dukan Receipt*\nItem: {item_choice}\nQty: {qty}\nTotal: ₹{total}"
        st.success(f"Bill for {item_choice} saved!")
        st.link_button("📲 Send WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        
    except Exception as e:
        st.error("Could not save sale. Please ensure your Supabase tables are set up correctly.")
        st.info("Check the SQL Editor script provided in the instructions.")
