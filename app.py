import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & SECRETS ---
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎", layout="wide")

URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]

@st.cache_resource
def get_db():
    return create_client(URL, KEY)

db = get_db()

# --- 2. MASTER PRODUCT LIST ---
MASTER_PRODUCTS = sorted([
    "Potato (Aloo)", "Onion (Pyaz)", "Tomato (Tamatar)", "Ginger (Adrak)", "Garlic (Lahsun)",
    "Green Chilli", "Lemon", "Coriander", "Mint (Pudina)", "Spinach (Palak)", 
    "Cauliflower", "Cabbage", "Lady Finger (Bhindi)", "Brinjal (Long)", "Brinjal (Round)",
    "Bottle Gourd (Lauki)", "Bitter Gourd (Karela)", "Ridge Gourd (Tori)", "Pumpkin",
    "Capsicum (Green)", "Carrot", "Radish (Mooli)", "Cucumber", "French Beans", 
    "Green Peas (Matar)", "Broccoli", "Mushroom", "Sweet Potato", "Beetroot", 
    "Apple (Shimla)", "Banana (Kela)", "Papaya", "Pomegranate (Anar)", "Guava", 
    "Orange", "Grapes (Green)", "Watermelon", "Mango (Safeda)", "Pineapple", "Chickoo"
])

# --- 3. UI ---
st.title("🏪 Apni Dukan")
menu = ["Billing", "Marketing & WhatsApp", "Inventory Manager", "Daily Reports"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- SECTION: BILLING ---
if choice == "Billing":
    st.header("📝 Create New Bill")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Customer Name")
                flat = st.text_input("Tower/Flat No")
            with col2:
                item_choice = st.selectbox("Select Item", df_inv["name"].tolist())
                qty = st.number_input("Quantity", min_value=0.1, step=0.1)
            
            if st.form_submit_button("Generate & Save Bill"):
                item_row = df_inv[df_inv["name"] == item_choice].iloc[0]
                total = item_row["sale_price"] * qty
                profit = (item_row["sale_price"] - item_row["cost_price"]) * qty
                
                db.table("sales").insert({
                    "item_name": item_choice, "qty": qty, 
                    "total_bill": total, "profit": profit, "tower_flat": flat
                }).execute()
                
                msg = f"*Apni Dukan Receipt*\n------------------\n*Customer:* {c_name}\n*Flat:* {flat}\n*Item:* {item_choice}\n*Qty:* {qty}\n*Total: ₹{total}*\n------------------\nThank you!"
                st.success(f"Bill Saved: ₹{total}")
                st.link_button("📲 Share on WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
    else:
        st.warning("No items in shop! Add them in Inventory Manager.")

# --- SECTION: MARKETING ---
elif choice == "Marketing & WhatsApp":
    st.header("📢 Group Announcements")
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Create Daily Price List"):
                today = datetime.now().strftime("%d %b")
                msg = f"*🏪 Apni Dukan - Fresh Arrivals ({today})*\n\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                msg += "\n📞 Order now for home delivery!"
                st.link_button("🚀 Share to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        with col2:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("🔥 Create Flash Sale"):
                    msg = "⚡ *FLASH SALE - APNI DUKAN* ⚡\n\n"
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* at only *₹{row['sale_price']}* !!\n"
                    msg += "\n⏳ Limited time offer!"
                    st.link_button("🚀 Blast to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
            else:
                st.write("Mark items as 'Flash Sale' in Inventory first.")

# --- SECTION: INVENTORY ---
elif choice == "Inventory Manager":
    st.header("📦 Manage Stock")
    with st.expander("➕ Add New Item to Shop"):
        with st.form("add_form", clear_on_submit=True):
            p_name = st.selectbox("Select Product", MASTER_PRODUCTS)
            c_price = st.number_input("Cost Price (Buy)", min_value=0.0)
            s_price = st.number_input("Sale Price (Sell)", min_value=0.0)
            is_flash = st.checkbox("Mark as Flash Sale?")
            if st.form_submit_button("Add to Shop"):
                db.table("inventory").upsert({
                    "name": p_name, "cost_price": c_price, "sale_price": s_price, "is_flash_sale": is_flash
                }).execute()
                st.success(f"Added/Updated {p_name}")
                st.rerun()

    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.subheader("Current Price List")
        edited = st.data_editor(df, num_rows="dynamic", key="inv_edit", hide_index=True)
        if st.button("💾 Save Changes"):
            for _, row in edited.iterrows():
                db.table("inventory").upsert({
                    "id": row["id"], "name": row["name"], 
                    "cost_price": row["cost_price"], "sale_price": row["sale_price"],
                    "is_flash_sale": row["is_flash_sale"]
                }).execute()
            st.success("Cloud Updated!")

# --- SECTION: REPORTS ---
elif choice == "Daily Reports":
    st.header("📊 Business Analytics")
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        col1, col2 = st.columns(2)
        col1.metric("Total Sales", f"₹{sdf['total_bill'].sum()}")
        col2.metric("Total Profit", f"₹{sdf['profit'].sum()}")
        
        st.subheader("Sale History")
        st.dataframe(sdf[["created_at", "item_name", "qty", "total_bill", "tower_flat"]], use_container_width=True)
    else:
        st.info("No sales recorded today.")
