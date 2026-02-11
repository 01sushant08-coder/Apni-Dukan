import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. INITIALIZATION & SECRETS ---
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎")

# Fetching credentials from Streamlit Secrets
try:
    URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
    KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
except KeyError:
    st.error("Secrets not found! Please check your Streamlit Cloud settings.")
    st.stop()

@st.cache_resource
def get_db_client():
    return create_client(URL, KEY)

db = get_db_client()

# --- 2. UTILITY FUNCTIONS ---
def get_inventory():
    try:
        res = db.table("inventory").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return pd.DataFrame()

# --- 3. UI LAYOUT ---
st.title("🏪 Apni Dukan")
st.markdown(f"**Date:** {datetime.now().strftime('%d %b %Y')}")

menu = ["Billing & WhatsApp", "Inventory Manager", "Daily Reports"]
choice = st.sidebar.selectbox("Navigate Menu", menu)

# --- SECTION 1: BILLING ---
if choice == "Billing & WhatsApp":
    st.header("📝 Create a Bill")
    df_inv = get_inventory()
    
    if df_inv.empty:
        st.info("Your inventory is empty. Go to 'Inventory Manager' to add items.")
    else:
        with st.form("bill_form"):
            col1, col2 = st.columns(2)
            with col1:
                cust_name = st.text_input("Customer Name")
                tower_flat = st.text_input("Tower & Flat (e.g. T4-101)")
            with col2:
                # Create a list of names for the dropdown
                item_list = df_inv["name"].tolist()
                selected_item = st.selectbox("Select Fruit/Veggie", item_list)
                qty = st.number_input("Quantity (kg/units)", min_value=0.1, step=0.1)
            
            submit_bill = st.form_submit_button("Generate & Share")

            if submit_bill:
                # Find item pricing from inventory
                item_data = df_inv[df_inv["name"] == selected_item].iloc[0]
                total_price = item_data["sale_price"] * qty
                total_profit = (item_data["sale_price"] - item_data["cost_price"]) * qty
                
                # Save to Sales Table in Supabase
                sale_entry = {
                    "item_name": selected_item,
                    "qty": qty,
                    "total_bill": total_price,
                    "profit": total_profit,
                    "tower_flat": tower_flat
                }
                db.table("sales").insert(sale_entry).execute()
                
                # WhatsApp Formatting
                bill_msg = (
                    f"*Apni Dukan - Order Receipt*\n"
                    f"Customer: {cust_name}\n"
                    f"Location: {tower_flat}\n"
                    f"------------------\n"
                    f"Item: {selected_item}\n"
                    f"Qty: {qty}\n"
                    f"*Total Amount: ₹{total_price}*\n"
                    f"------------------\n"
                    f"Thank you for shopping at Apni Dukan!"
                )
                
                whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(bill_msg)}"
                st.success(f"Bill for ₹{total_price} saved successfully!")
                st.link_button("📲 Share on WhatsApp", whatsapp_url)

# --- SECTION 2: INVENTORY ---
elif choice == "Inventory Manager":
    st.header("📦 Manage Stock")
    
    # Add Item Form
    with st.expander("➕ Add New Item"):
        with st.form("add_item_form", clear_on_submit=True):
            name = st.text_input("Product Name")
            cp = st.number_input("Cost Price (Buy)", min_value=0.0)
            sp = st.number_input("Sale Price (Sell)", min_value=0.0)
            if st.form_submit_button("Add to List"):
                db.table("inventory").insert({"name": name, "cost_price": cp, "sale_price": sp}).execute()
                st.success(f"{name} added!")
                st.rerun()

    # Show and Edit/Delete Items
    st.subheader("Current Inventory")
    df_current = get_inventory()
    if not df_current.empty:
        # data_editor allows row deletion and editing
        edited_df = st.data_editor(df_current, num_rows="dynamic", key="inv_table", hide_index=True)
        
        if st.button("💾 Sync All Changes"):
            # Upsert handles both updates and new rows
            for _, row in edited_df.iterrows():
                db.table("inventory").upsert({
                    "id": row["id"],
                    "name": row["name"],
                    "cost_price": row["cost_price"],
                    "sale_price": row["sale_price"]
                }).execute()
            st.success("Cloud inventory updated!")

# --- SECTION 3: REPORTS ---
elif choice == "Daily Reports":
    st.header("📊 Sales Analytics")
    try:
        sales_res = db.table("sales").select("*").execute()
        if sales_res.data:
            df_sales = pd.DataFrame(sales_res.data)
            
            c1, c2 = st.columns(2)
            c1.metric("Total Sales (Revenue)", f"₹{df_sales['total_bill'].sum():.2f}")
            c2.metric("Net Profit", f"₹{df_sales['profit'].sum():.2f}")
            
            st.subheader("Transaction History")
            st.dataframe(df_sales[["created_at", "item_name", "qty", "total_bill", "tower_flat"]], use_container_width=True)
        else:
            st.info("No sales data recorded yet.")
    except:
        st.error("Could not load reports.")
