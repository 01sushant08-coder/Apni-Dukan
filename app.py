import streamlit as st
from st_supabase_connection import SupabaseConnection
import urllib.parse
import pandas as pd

# Page Config
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎")

# Initialize Connection to Supabase
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🏪 Apni Dukan: Admin Portal")

menu = ["Inventory Manager", "Billing & WhatsApp", "Daily Reports"]
choice = st.sidebar.selectbox("Go to", menu)

# --- 1. INVENTORY MANAGER (Add/Delete/Edit) ---
if choice == "Inventory Manager":
    st.header("📦 Product List")
    
    # Fetch current list from Cloud
    items = conn.query("*", table="inventory", ttl="0s").execute()
    df = pd.DataFrame(items.data)
    
    # Feature: Add New Item
    with st.expander("➕ Add New Fruit/Vegetable"):
        with st.form("add_form", clear_on_submit=True):
            new_name = st.text_input("Item Name (e.g., Mango)")
            c_price = st.number_input("Cost Price (Buy Price)", min_value=0.0)
            s_price = st.number_input("Sale Price (Sell Price)", min_value=0.0)
            if st.form_submit_button("Add to Shop"):
                conn.table("inventory").insert({"name": new_name, "cost_price": c_price, "sale_price": s_price}).execute()
                st.success(f"{new_name} added!")
                st.rerun()

    # Feature: Edit & Delete
    if not df.empty:
        st.subheader("Edit Prices or Remove Items")
        # The data_editor allows adding/deleting rows directly
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor", hide_index=True)
        
        if st.button("💾 Save All Changes"):
            # This logic syncs the table back to the cloud
            for index, row in edited_df.iterrows():
                conn.table("inventory").upsert({
                    "id": row['id'], 
                    "name": row['name'], 
                    "cost_price": row['cost_price'], 
                    "sale_price": row['sale_price']
                }).execute()
            st.success("Inventory synced to cloud!")

# --- 2. BILLING & WHATSAPP ---
elif choice == "Billing & WhatsApp":
    st.header("📝 Create Bill")
    items_data = conn.query("name, sale_price, cost_price", table="inventory").execute().data
    
    col1, col2 = st.columns(2)
    with col1:
        cust_name = st.text_input("Customer Name")
        tower_flat = st.text_input("Tower & Flat No (e.g., T2-405)")
    with col2:
        selected = st.selectbox("Select Item", [i['name'] for i in items_data])
        qty = st.number_input("Quantity (kg/units)", min_value=0.1)

    if st.button("Generate & Save Bill"):
        item_info = next(i for i in items_data if i['name'] == selected)
        total = item_info['sale_price'] * qty
        profit = (item_info['sale_price'] - item_info['cost_price']) * qty
        
        # Save to Sales Table
        conn.table("sales").insert({
            "item_name": selected, "qty": qty, 
            "total_bill": total, "profit": profit, "tower_flat": tower_flat
        }).execute()
        
        # Format WhatsApp Message
        msg = f"*Apni Dukan - Digital Receipt*\n\nCustomer: {cust_name}\nFlat: {tower_flat}\n---\nItem: {selected}\nQty: {qty}\n*Total: ₹{total}*\n\nThank you for shopping with us!"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
        
        st.success(f"Bill Saved! Total: ₹{total}")
        st.link_button("📲 Share Bill on WhatsApp", whatsapp_url)

# --- 3. REPORTS ---
elif choice == "Daily Reports":
    st.header("📊 Sales & Profit")
    sales_data = conn.query("*", table="sales").execute()
    if sales_data.data:
        sdf = pd.DataFrame(sales_data.data)
        st.metric("Total Shop Revenue", f"₹{sdf['total_bill'].sum()}")
        st.metric("Total Net Profit", f"₹{sdf['profit'].sum()}")
        st.subheader("Transaction History")
        st.dataframe(sdf[['created_at', 'item_name', 'total_bill', 'tower_flat']], hide_index=True)
    else:
        st.info("No sales recorded yet.")
