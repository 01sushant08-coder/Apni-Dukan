import streamlit as st
from st_supabase_connection import SupabaseConnection
import urllib.parse
import pandas as pd

# Initialize Connection
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🍏 FreshCart Manager")

menu = ["Inventory & Prices", "Billing", "Reports"]
choice = st.sidebar.selectbox("Menu", menu)

# --- INVENTORY & PRICE MANAGEMENT ---
if choice == "Inventory & Prices":
    st.header("Manage Inventory")
    
    # Fetch Data
    items = conn.query("*", table="inventory", ttl="0s").execute()
    df = pd.DataFrame(items.data)
    
    # Editable Table (Add/Delete/Edit)
    edited_df = st.data_editor(df, num_rows="dynamic", key="inv_editor")
    
    if st.button("Save Changes"):
        # Logic to sync edited_df back to Supabase
        # (For simplicity, you can upsert the rows here)
        st.success("Inventory Updated!")

    # Daily Price List for WhatsApp
    if st.button("Generate WhatsApp Daily List"):
        msg = "Today's Prices:\n"
        for _, row in df.iterrows():
            msg += f"- {row['name']}: ₹{row['sale_price']}/kg\n"
        
        encoded_msg = urllib.parse.quote(msg)
        st.link_button("Share Daily List on WhatsApp", f"https://wa.me/?text={encoded_msg}")

# --- BILLING SYSTEM ---
elif choice == "Billing":
    st.header("Create New Bill")
    items_data = conn.query("name, sale_price, cost_price", table="inventory").execute().data
    item_names = [i['name'] for i in items_data]
    
    with st.form("bill_form"):
        cust_loc = st.text_input("Tower & Flat No")
        selected = st.selectbox("Select Item", item_names)
        qty = st.number_input("Quantity", min_value=0.1)
        
        if st.form_submit_button("Finalize Bill"):
            # Find item details
            item_info = next(i for i in items_data if i['name'] == selected)
            total = item_info['sale_price'] * qty
            profit = (item_info['sale_price'] - item_info['cost_price']) * qty
            
            # Save to Database
            conn.table("sales").insert({
                "item_name": selected, "qty": qty, 
                "total_bill": total, "profit": profit, "tower_flat": cust_loc
            }).execute()
            
            # Share via WhatsApp
            bill_txt = f"Bill for {cust_loc}:\nItem: {selected}\nQty: {qty}\nTotal: ₹{total}"
            st.link_button("Send Bill via WhatsApp", f"https://wa.me/?text={urllib.parse.quote(bill_txt)}")

# --- REPORTS ---
elif choice == "Reports":
    st.header("Sales Performance")
    sales_data = conn.query("*", table="sales").execute()
    sales_df = pd.DataFrame(sales_data.data)
    
    st.metric("Total Revenue", f"₹{sales_df['total_bill'].sum()}")
    st.metric("Total Profit", f"₹{sales_df['profit'].sum()}")
    st.bar_chart(sales_df, x="created_at", y="profit")
