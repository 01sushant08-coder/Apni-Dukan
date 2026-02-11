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

# --- 2. CSS FOR VISIBILITY & BRANDING ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    label, p, .stMarkdown {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    [data-testid="stSidebar"] { background-color: #2e5a27 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3 { color: #2e5a27 !important; text-align: center; }
    .stButton>button {
        background-color: #e67e22 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        height: 50px;
    }
    footer {visibility: hidden;}
    .footer-custom {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #f1f1f1; color: #2e5a27;
        text-align: center; padding: 10px; font-weight: bold;
        border-top: 2px solid #2e5a27; z-index: 999;
    }
    </style>
    <div class="footer-custom">Created by Sushant</div>
    """, unsafe_allow_html=True)

# --- 3. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 4. DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = ["001", "002", "003", "004"] 
for floor in range(1, 19):
    for flat in range(1, 5):
        FLATS.append(f"{floor}{flat:02d}")

# --- 5. NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

if st.sidebar.button("🏠 Back to Home"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- SECTION: HOME DASHBOARD ---
if st.session_state.page == "🏠 Home":
    st.title("🌿 Apni Dukan")
    st.subheader("Fresh Quality. Local Service.")
    
    if st.button("📦 Inventory Manager"):
        st.session_state.page = "📦 Inventory Manager"; st.rerun()
    if st.button("📢 Marketing"):
        st.session_state.page = "📢 Marketing"; st.rerun()
    if st.button("📝 Billing"):
        st.session_state.page = "📝 Billing"; st.rerun()
    if st.button("📊 Daily Reports"):
        st.session_state.page = "📊 Daily Reports"; st.rerun()

# --- SECTION: INVENTORY MANAGER ---
elif st.session_state.page == "📦 Inventory Manager":
    st.header("📦 Inventory Manager")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.expander("⚙️ Add New Item to Master List"):
        new_item = st.text_input("New Item Name")
        if st.button("Add Now"):
            if new_item:
                db.table("master_list").upsert({"name": new_item}).execute()
                st.success(f"{new_item} added!")
                st.rerun()

    try:
        m_res = db.table("master_list").select("*").execute()
        m_opts = sorted([i['name'] for i in m_res.data]) if m_res.data else ["Potato (Aloo)"]
    except: m_opts = ["Potato (Aloo)"]

    with st.form("inv_form", clear_on_submit=True):
        p_name = st.selectbox("Select Product", m_opts)
        c_p = st.number_input("Cost Price (Buy)", min_value=0.0)
        s_p = st.number_input("Sale Price (Sell)", min_value=0.0)
        flash = st.checkbox("Include in Flash Sale?")
        if st.form_submit_button("Update Inventory"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_p, "sale_price": s_p, "is_flash_sale": flash}).execute()
            st.success("Updated!")

# --- SECTION: MARKETING (NEW ATTRACTIVE THEME) ---
elif st.session_state.page == "📢 Marketing":
    st.header("📢 WhatsApp Marketing")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        msg_type = st.radio("Message Style:", ["🌿 Daily Fresh List", "⚡ Flash Sale Blast"], horizontal=True)
        
        contact_info = "\n\n📞 *Contact at: 9654399817 for orders*"
        
        if "Daily" in msg_type:
            if st.button("Generate & Copy Daily List"):
                msg = f"🌿 *APNI DUKAN - FRESH ARRIVALS* 🌿\n"
                msg += f"📅 _Date: {datetime.now().strftime('%d %b, %Y')}_\n"
                msg += "--------------------------------\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"✅ {row['name']}: *₹{row['sale_price']}*\n"
                msg += "--------------------------------"
                msg += "\n🚚 *Free Home Delivery Available!*"
                msg += contact_info
                
                st.link_button("🚀 Send to WhatsApp Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("Generate & Copy Flash Sale"):
                    msg = "⚡ *FLASH SALE ALERT - APNI DUKAN* ⚡\n"
                    msg += "🔥 _Prices Slashed for Limited Time!_ 🔥\n\n"
                    for _, row in flash_df.iterrows():
                        # Using strikethrough for a 'sale' effect
                        old_price = round(row['sale_price'] * 1.2, 0)
                        msg += f"📦 *{row['name']}*\n💰 Now: *₹{row['sale_price']}* (Was ~₹{old_price}~)\n\n"
                    msg += "⏳ _Offer valid until stock lasts!_"
                    msg += contact_info
                    
                    st.link_button("🚀 Blast Flash Sale", f"https://wa.me/?text={urllib.parse.quote(msg)}")
            else:
                st.info("No items marked for Flash Sale in Inventory.")

# --- SECTION: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.header("📝 Create New Bill")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            name = st.text_input("Customer Name")
            tow = st.selectbox("Tower", TOWERS)
            flt = st.selectbox("Flat No", FLATS)
            itm = st.selectbox("Item", df_inv["name"].tolist())
            unt = st.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Quantity", min_value=0.1)
            
            if st.form_submit_button("Generate Bill"):
                row = df_inv[df_inv["name"] == itm].iloc[0]
                c_qty = qty/1000 if unt == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                prof = round((row["sale_price"] - row["cost_price"]) * c_qty, 2)
                
                db.table("sales").insert({"item_name": itm, "qty": f"{qty} {unt}", "total_bill": tot, "profit": prof, "tower_flat": f"T-{tow} {flt}"}).execute()
                
                msg = f"*Apni Dukan - Digital Receipt*\n--------------------------\n👤 *Cust:* {name}\n📍 *Loc:* T-{tow} {flt}\n🥦 *Item:* {itm}\n⚖️ *Qty:* {qty}{unt}\n💰 *Total: ₹{tot}*\n--------------------------\nThank you for shopping!"
                st.link_button("📲 Send Bill", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION: REPORTS ---
elif st.session_state.page == "📊 Daily Reports":
    st.header("📊 Daily Reports")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        c1, c2 = st.columns(2)
        with c1: st.metric("Total Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        with c2: st.metric("Total Profit", f"₹{sdf['profit'].sum():.2f}")
        
        st.subheader("Transaction History")
        st.dataframe(sdf[["created_at", "item_name", "qty", "total_bill", "tower_flat"]], use_container_width=True)
    else:
        st.info("No sales recorded yet.")
