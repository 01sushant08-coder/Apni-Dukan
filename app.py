import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- INITIALIZATION ---
st.set_page_config(page_title="Apni Dukan Manager", page_icon="🍎")
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]

@st.cache_resource
def get_db():
    return create_client(URL, KEY)
db = get_db()

st.title("🏪 Apni Dukan")
menu = ["Billing", "Marketing & WhatsApp", "Inventory Manager", "Reports"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- NEW: MARKETING & WHATSAPP GROUP MESSAGES ---
if choice == "Marketing & WhatsApp":
    st.header("📢 Group Announcements")
    res = db.table("inventory").select("*").execute()
    df = pd.DataFrame(res.data)

    if df.empty:
        st.warning("No items in inventory to announce!")
    else:
        col1, col2 = st.columns(2)
        
        # FEATURE 1: DAILY PRICE LIST
        with col1:
            st.subheader("Daily Price List")
            if st.button("📝 Create Daily List"):
                # Professional WhatsApp Formatting
                today = datetime.now().strftime("%d %b")
                msg = f"*🏪 Apni Dukan - Fresh Arrivals ({today})*\n\n"
                msg += "Prices for today:\n"
                
                # Sort by name and add to message
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                
                msg += "\n📍 Location: [Your Shop Location]\n📞 Order now for home delivery!"
                
                whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                st.info("Message ready for Group!")
                st.link_button("🚀 Share to Group", whatsapp_url)

        # FEATURE 2: FLASH SALE
        with col2:
            st.subheader("Flash Sale Blast")
            # Only pick items marked as Flash Sale
            flash_df = df[df["is_flash_sale"] == True]
            
            if flash_df.empty:
                st.write("No items marked for Flash Sale. Go to 'Inventory' to mark them.")
            else:
                if st.button("🔥 Create Flash Sale"):
                    msg = "⚡ *FLASH SALE - APNI DUKAN* ⚡\n"
                    msg += "_Grab them before they are gone!_\n\n"
                    
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* @ ~₹{row['sale_price'] + 10}~ *₹{row['sale_price']}* !!\n"
                    
                    msg += "\n⏳ Offer valid for next 2 hours only!\n📍 Visit us at Apni Dukan."
                    
                    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"
                    st.link_button("🚀 Blast to Group", whatsapp_url)

# --- UPDATED INVENTORY MANAGER (With Flash Sale Toggle) ---
elif choice == "Inventory Manager":
    st.header("📦 Stock & Flash Sale Settings")
    res = db.table("inventory").select("*").execute()
    df = pd.DataFrame(res.data)
    
    # Dropdown to add items
    # ... (Same as previous dropdown code) ...

    if not df.empty:
        st.write("Toggle the 'is_flash_sale' box to include items in the Flash Sale blast.")
        edited = st.data_editor(df, num_rows="dynamic", key="main_inv", hide_index=True)
        
        if st.button("💾 Save All Changes"):
            for _, row in edited.iterrows():
                db.table("inventory").upsert({
                    "id": row["id"], 
                    "name": row["name"], 
                    "cost_price": row["cost_price"], 
                    "sale_price": row["sale_price"],
                    "is_flash_sale": row["is_flash_sale"] # NEW COLUMN
                }).execute()
            st.success("Changes saved!")
            
# --- BILLING & REPORTS ---
# ... (Keep previous billing/report code) ...
