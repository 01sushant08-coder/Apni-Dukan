import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- INITIALIZATION ---
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎", layout="centered")

# Access secrets from Streamlit Cloud settings
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]

@st.cache_resource
def get_client():
    return create_client(URL, KEY)

db = get_client()

# --- APP HEADER ---
st.title("🏪 Apni Dukan")
st.subheader("Inventory & Billing System")

menu = ["Billing & WhatsApp", "Inventory Manager", "Daily Reports"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- 1. BILLING & WHATSAPP ---
if choice == "Billing & WhatsApp":
    st.header("📝 New Sale")
    
    # Get items for dropdown
    items_res = db.table("inventory").select("*").execute()
    items_df = pd.DataFrame(items_res.data)
    
    if items_df.empty:
        st.warning("Please add items in 'Inventory Manager' first!")
    else:
        with st.form("billing_form", clear_on_submit=False):
            c_name = st.text_input("Customer Name")
            loc = st.text_input("Tower & Flat No (e.g., T1-102)")
            
            # Searchable dropdown
            selected_item_name = st.selectbox("Select Item", items_df["name"].tolist())
            qty = st.number_input("Quantity (kg/units)", min_value=0.0, step=0.5)
            
            if st.form_submit_button("Generate Bill"):
                # Get item details
                item_row = items_df[items_df["name"] == selected_item_name].iloc[0]
                total = item_row["sale_price"] * qty
                profit = (item_row["sale_price"] - item_row["cost_price"]) * qty
                
                # Save Sale to DB
                db.table("sales").insert({
                    "item_name": selected_item_name,
                    "qty": qty,
                    "total_bill": total,
                    "profit": profit,
                    "tower_flat": loc
                }).execute()
                
                # WhatsApp Formatting
                msg = f"*Apni Dukan - Receipt*\n\nCust: {c_name}\nLoc: {loc}\n---\n*Item:* {selected_item_name}\n*Qty:* {qty}\n*Total: ₹{total}*\n\nThank you!"
                whatsapp_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                
                st.success(f"Bill Generated: ₹{total}")
                st.link_button("📲 Send to WhatsApp", whatsapp_link)

# --- 2. INVENTORY MANAGER ---
elif choice == "Inventory Manager":
    st.header("📦 Manage Stock")
    
    # Fetch and show data
    res = db.table("inventory").select("*").execute()
    df = pd.DataFrame(res.data)
    
    with st.expander("➕ Add New Fruit/Vegetable"):
        with st.form("add_form", clear_on_submit=True):
            n = st.text_input("Item Name")
            cp = st.number_input("Cost Price", min_value=0.0)
            sp = st.number_input("Sale Price", min_value=0.0)
            if st.form_submit_button("Add Item"):
                db.table("inventory").insert({"name": n, "cost_price": cp, "sale_price": sp}).execute()
                st.success("Added!")
                st.rerun()

    if not df.empty:
        st.subheader("Current Price List")
        # Editable table for prices and deletion
        edited_df = st.data_editor(df, num_rows="dynamic", key="inv_editor", hide_index=True)
        
        if st.button("💾 Save Changes"):
            # Update data logic
            for _, row in edited_df.iterrows():
                db.table("inventory").upsert({
                    "id": row["id"], 
                    "name": row["name"], 
                    "cost_price": row["cost_price"], 
                    "sale_price": row["sale_price"]
                }).execute()
            st.success("All changes synced!")

# --- 3. REPORTS ---
elif choice == "Daily Reports":
    st.header("📊 Business Performance")
    sales_res = db.table("sales").select("*").execute()
    
    if sales_res.data:
        sdf = pd.DataFrame(sales_res.data)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue", f"₹{sdf['total_bill'].sum()}")
        col2.metric("Total Profit", f"₹{sdf['profit'].sum()}")
        
        st.subheader("History")
        st.dataframe(sdf[["created_at", "item_name", "total_bill", "tower_flat"]], use_container_width=True)
    else:
        st.info("No sales data available yet.")
