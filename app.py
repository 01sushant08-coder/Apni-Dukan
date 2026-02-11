import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
from datetime import datetime

# --- 1. CONFIG ---
st.set_page_config(
    page_title="Apni Dukan", 
    page_icon="🌿", 
    layout="centered", # Better for mobile "App" feel
    initial_sidebar_state="collapsed" 
)

# --- 2. THE "SMART" UI ENGINE (Modern CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    /* Force Light Mode & App Font */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #F4F7F5 !important;
        font-family: 'Inter', sans-serif !important;
        color: #1A1A1A !important;
    }

    /* Modern Glass Header */
    .app-header {
        background: linear-gradient(135deg, #2E5A27 0%, #1B3F16 100%);
        padding: 2rem 1rem;
        border-radius: 0 0 25px 25px;
        margin: -6rem -2rem 2rem -2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .app-header h1 {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        letter-spacing: -1px;
        margin: 0;
    }

    /* Smart Cards for Forms */
    div[data-testid="stForm"], .stChatMessage, .stExpander {
        background-color: #FFFFFF !important;
        border: none !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* Readable Labels */
    label, .stMarkdown p {
        color: #2E5A27 !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px;
        margin-bottom: 8px !important;
    }

    /* High-Visibility Inputs */
    input, select, .stSelectbox div {
        background-color: #F9F9F9 !important;
        border: 2px solid #E0E0E0 !important;
        border-radius: 12px !important;
        color: #1A1A1A !important;
        height: 50px !important;
    }

    /* Modern "Squircle" Buttons */
    .stButton>button {
        background: #E67E22 !important;
        color: white !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(230, 126, 34, 0.3) !important;
        width: 100%;
    }
    .stButton>button:active {
        transform: scale(0.98);
        background: #D35400 !important;
    }

    /* Hide default junk */
    #MainMenu, footer, header {visibility: hidden;}
    
    .sushant-footer {
        text-align: center;
        padding: 2rem;
        color: #A0A0A0;
        font-size: 0.9rem;
        font-weight: 700;
    }
    </style>
    
    <div class="app-header">
        <h1>Apni Dukan</h1>
    </div>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = ["001", "002", "003", "004"] + [f"{floor}{flat:02d}" for floor in range(1, 19) for flat in range(1, 5)]

if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

# Sidebar Navigation (Hidden but accessible via icon)
if st.sidebar.button("🏠 Home Menu"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- 4. NAVIGATION SECTIONS ---
if st.session_state.page == "🏠 Home":
    st.write("### Welcome Back!")
    if st.button("📦 Manage Inventory"): st.session_state.page = "📦 Inventory Manager"; st.rerun()
    if st.button("📢 WhatsApp Marketing"): st.session_state.page = "📢 Marketing"; st.rerun()
    if st.button("📝 Create New Bill"): st.session_state.page = "📝 Billing"; st.rerun()
    if st.button("📊 View Reports"): st.session_state.page = "📊 Daily Reports"; st.rerun()

elif st.session_state.page == "📦 Inventory Manager":
    st.write("### 📦 Inventory")
    if st.button("← Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.form("inv_form"):
        # Fetching Master List
        try:
            m_res = db.table("master_list").select("name").execute()
            m_opts = sorted([i['name'] for i in m_res.data])
        except: m_opts = ["Add items in Master List first"]
        
        p_name = st.selectbox("PRODUCT", m_opts)
        c_p = st.number_input("COST PRICE", min_value=0.0)
        s_p = st.number_input("SELLING PRICE", min_value=0.0)
        flash = st.checkbox("MARK FOR FLASH SALE")
        if st.form_submit_button("UPDATE SHOP PRICE"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_p, "sale_price": s_p, "is_flash_sale": flash}).execute()
            st.balloons()

elif st.session_state.page == "📝 Billing":
    st.write("### 📝 New Bill")
    if st.button("← Back"): st.session_state.page = "🏠 Home"; st.rerun()
    
    inv_res = db.table("inventory").select("*").execute()
    if inv_res.data:
        df_inv = pd.DataFrame(inv_res.data)
        with st.form("bill"):
            c_name = st.text_input("CUSTOMER NAME")
            col1, col2 = st.columns(2)
            tow = col1.selectbox("TOWER", TOWERS)
            flt = col2.selectbox("FLAT", FLATS)
            item = st.selectbox("ITEM", df_inv["name"].tolist())
            u_col1, u_col2 = st.columns(2)
            unit = u_col1.selectbox("UNIT", ["kg", "gms", "Dozen", "Piece"])
            qty = u_col2.number_input("QTY", min_value=0.1)
            
            if st.form_submit_button("GENERATE & SEND"):
                row = df_inv[df_inv["name"] == item].iloc[0]
                c_qty = qty/1000 if unit == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                db.table("sales").insert({"item_name": item, "qty": f"{qty} {unit}", "total_bill": tot, "tower_flat": f"T-{tow}-{flt}"}).execute()
                msg = f"*Apni Dukan Receipt*\n*Cust:* {c_name}\n*Item:* {item}\n*Total: ₹{tot}*"
                st.link_button("📲 SEND TO WHATSAPP", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# (Similar logic for Marketing and Reports...)

st.markdown('<div class="sushant-footer">DESIGNED BY SUSHANT</div>', unsafe_allow_html=True)
