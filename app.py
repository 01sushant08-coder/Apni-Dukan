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

# --- 2. HIGH-CONTRAST "SAFE" CSS ---
st.markdown("""
    <style>
    /* Force a standard white background */
    .stApp { background-color: #FFFFFF !important; }
    
    /* MAIN HEADER: Dark Green background, White text */
    .main-header {
        background-color: #1B3F16 !important;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #FFFFFF !important;
        margin: 0;
        text-align: center;
        font-size: 2rem !important;
    }

    /* ALL LABELS AND TEXT: Force Pure Black */
    label, p, span, .stMarkdown, .stSelectbox label, .stNumberInput label {
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.1rem !important;
    }

    /* INPUT BOXES: Force white background with black text */
    input, select, .stSelectbox div {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 1px solid #1B3F16 !important;
    }

    /* BUTTONS: Safety Orange with White Text */
    .stButton>button {
        background-color: #E67E22 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 1.2rem !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }

    /* SIDEBAR: Dark Green */
    [data-testid="stSidebar"] { background-color: #1B3F16 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    /* FOOTER */
    footer {visibility: hidden;}
    .footer-custom {
        text-align: center;
        color: #1B3F16;
        font-weight: bold;
        padding: 20px;
        border-top: 1px solid #1B3F16;
    }
    </style>
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

if st.sidebar.button("🏠 Home Menu"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- HEADER SECTION ---
st.markdown('<div class="main-header"><h1>🌿 Apni Dukan</h1></div>', unsafe_allow_html=True)

# --- SECTION: HOME ---
if st.session_state.page == "🏠 Home":
    st.subheader("Select a Task")
    if st.button("📦 Inventory Manager"):
        st.session_state.page = "📦 Inventory Manager"; st.rerun()
    st.write("") # Spacer
    if st.button("📢 Marketing"):
        st.session_state.page = "📢 Marketing"; st.rerun()
    st.write("") # Spacer
    if st.button("📝 Billing"):
        st.session_state.page = "📝 Billing"; st.rerun()
    st.write("") # Spacer
    if st.button("📊 Daily Reports"):
        st.session_state.page = "📊 Daily Reports"; st.rerun()

# --- SECTION: INVENTORY ---
elif st.session_state.page == "📦 Inventory Manager":
    st.write("### 📦 Inventory Manager")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.expander("⚙️ Add New Item to Master"):
        new_item = st.text_input("New Item Name")
        if st.button("Add Now"):
            if new_item:
                db.table("master_list").upsert({"name": new_item}).execute()
                st.success("Done!")
                st.rerun()

    try:
        m_res = db.table("master_list").select("*").execute()
        m_opts = sorted([i['name'] for i in m_res.data]) if m_res.data else ["Potato"]
    except: m_opts = ["Potato"]

    with st.form("inv_form", clear_on_submit=True):
        p_name = st.selectbox("Product", m_opts)
        c_p = st.number_input("Cost (Buy)", min_value=0.0)
        s_p = st.number_input("Sale (Sell)", min_value=0.0)
        flash = st.checkbox("Flash Sale?")
        if st.form_submit_button("Update Prices"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_p, "sale_price": s_p, "is_flash_sale": flash}).execute()
            st.success("Updated!")

# --- SECTION: MARKETING ---
elif st.session_state.page == "📢 Marketing":
    st.write("### 📢 Marketing")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        msg_type = st.selectbox("Message Style:", ["Daily Price List", "Flash Sale Blast"])
        contact = "\n\n📞 *Contact: 9654399817*"
        
        if "Daily" in msg_type:
            if st.button("Share Daily List"):
                msg = f"🌿 *APNI DUKAN - FRESH LIST*\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"✅ {row['name']}: *₹{row['sale_price']}*\n"
                msg += contact
                st.link_button("🚀 WhatsApp Share", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else:
            flash_df = df[df["is_flash_sale"] == True]
            if st.button("Share Flash Sale"):
                msg = "⚡ *FLASH SALE ALERT* ⚡\n"
                for _, row in flash_df.iterrows():
                    msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}*!\n"
                msg += contact
                st.link_button("🚀 WhatsApp Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.write("### 📝 New Bill")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            name = st.text_input("Customer Name")
            tow = st.selectbox("Tower", TOWERS)
            flt = st.selectbox("Flat", FLATS)
            itm = st.selectbox("Item", df_inv["name"].tolist())
            unt = st.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Quantity", min_value=0.1)
            
            if st.form_submit_button("Generate Bill"):
                row = df_inv[df_inv["name"] == itm].iloc[0]
                c_qty = qty/1000 if unt == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                prof = round((row["sale_price"] - row["cost_price"]) * c_qty, 2)
                db.table("sales").insert({"item_name": itm, "qty": f"{qty} {unt}", "total_bill": tot, "profit": prof, "tower_flat": f"T-{tow} {flt}"}).execute()
                msg = f"*Receipt*\n*Cust:* {name}\n*Loc:* T-{tow} {flt}\n*Item:* {itm}\n*Total: ₹{tot}*"
                st.link_button("📲 Send WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION: REPORTS ---
elif st.session_state.page == "📊 Daily Reports":
    st.write("### 📊 Daily Reports")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        st.metric("Total Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        st.metric("Total Profit", f"₹{sdf['profit'].sum():.2f}")
        st.dataframe(sdf, use_container_width=True)

st.markdown('<div class="footer-custom">Created by Sushant</div>', unsafe_allow_html=True)
