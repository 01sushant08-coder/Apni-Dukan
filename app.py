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

# --- 2. THEME OVERHAUL (FOR MAXIMUM READABILITY) ---
st.markdown("""
    <style>
    /* 1. Main Background and Text */
    .stApp { background-color: #FFFFFF !important; }
    
    /* 2. Force all text to be Deep Black for contrast */
    label, p, .stMarkdown, .stSelectbox label, .stNumberInput label {
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
    }
    
    /* 3. Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #1B3F16 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* 4. Button Styling (Static Colors - No "Blackouts") */
    .stButton>button {
        background-color: #E67E22 !important; /* Safety Orange */
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: 2px solid #D35400 !important;
        width: 100% !important;
        height: 3rem !important;
        opacity: 1 !important;
    }
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
        background-color: #D35400 !important;
        color: #FFFFFF !important;
    }

    /* 5. Radio/Tabs Styling (Marketing Selection) */
    div[data-testid="stMarkdownContainer"] > p { color: #000000 !important; }
    .st-emotion-cache-16idsys p { color: #000000 !important; }
    
    /* Fix for Radio buttons appearing black */
    div[role="radiogroup"] {
        background-color: #F0F2F6 !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }

    /* 6. Footer */
    footer {visibility: hidden;}
    .footer-custom {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #F8F9FA; color: #1B3F16;
        text-align: center; padding: 10px; font-weight: bold;
        border-top: 2px solid #1B3F16; z-index: 999;
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

# --- SECTION: HOME ---
if st.session_state.page == "🏠 Home":
    st.title("🌿 Apni Dukan")
    st.subheader("Select a Section")
    
    if st.button("📦 Inventory Manager"):
        st.session_state.page = "📦 Inventory Manager"; st.rerun()
    if st.button("📢 Marketing"):
        st.session_state.page = "📢 Marketing"; st.rerun()
    if st.button("📝 Billing"):
        st.session_state.page = "📝 Billing"; st.rerun()
    if st.button("📊 Daily Reports"):
        st.session_state.page = "📊 Daily Reports"; st.rerun()

# --- SECTION: INVENTORY ---
elif st.session_state.page == "📦 Inventory Manager":
    st.header("📦 Inventory Manager")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.expander("⚙️ Add New Item to Master List"):
        new_item = st.text_input("Item Name")
        if st.button("Add Now"):
            if new_item:
                db.table("master_list").upsert({"name": new_item}).execute()
                st.success("Added!")
                st.rerun()

    try:
        m_res = db.table("master_list").select("*").execute()
        m_opts = sorted([i['name'] for i in m_res.data]) if m_res.data else ["Potato"]
    except: m_opts = ["Potato"]

    with st.form("inv_form", clear_on_submit=True):
        st.write("### Update Price")
        p_name = st.selectbox("Product", m_opts)
        c_p = st.number_input("Cost (Buy)", min_value=0.0)
        s_p = st.number_input("Sale (Sell)", min_value=0.0)
        flash = st.checkbox("Flash Sale?")
        if st.form_submit_button("Update Inventory"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_p, "sale_price": s_p, "is_flash_sale": flash}).execute()
            st.success("Updated!")

# --- SECTION: MARKETING ---
elif st.session_state.page == "📢 Marketing":
    st.header("📢 Marketing")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        msg_type = st.radio("Style:", ["Daily List", "Flash Sale"], horizontal=True)
        
        contact = "\n\n📞 *Contact: 9654399817 for orders*"
        
        if msg_type == "Daily List":
            if st.button("Generate Daily List"):
                msg = f"🌿 *APNI DUKAN - FRESH ARRIVALS* 🌿\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"✅ {row['name']}: *₹{row['sale_price']}*\n"
                msg += contact
                st.link_button("🚀 Share to WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("Generate Flash Blast"):
                    msg = "⚡ *FLASH SALE ALERT* ⚡\n"
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}*!\n"
                    msg += contact
                    st.link_button("🚀 Send Flash Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.header("📝 Create Bill")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            name = st.text_input("Cust Name")
            tow = st.selectbox("Tower", TOWERS)
            flt = st.selectbox("Flat", FLATS)
            itm = st.selectbox("Item", df_inv["name"].tolist())
            unt = st.selectbox("Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Qty", min_value=0.1)
            
            if st.form_submit_button("Generate & Save Bill"):
                row = df_inv[df_inv["name"] == itm].iloc[0]
                c_qty = qty/1000 if unt == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                prof = round((row["sale_price"] - row["cost_price"]) * c_qty, 2)
                db.table("sales").insert({"item_name": itm, "qty": f"{qty} {unt}", "total_bill": tot, "profit": prof, "tower_flat": f"T-{tow} {flt}"}).execute()
                msg = f"*Apni Dukan Receipt*\n*Cust:* {name}\n*Loc:* T-{tow} {flt}\n*Item:* {itm}\n*Total: ₹{tot}*"
                st.link_button("📲 Send WhatsApp Bill", f"https://wa.me/?text={urllib.parse.quote(msg)}")

# --- SECTION: REPORTS ---
elif st.session_state.page == "📊 Daily Reports":
    st.header("📊 Daily Reports")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    res = db.table("sales").select("*").execute()
    if res.data:
        sdf = pd.DataFrame(res.data)
        st.metric("Total Revenue", f"₹{sdf['total_bill'].sum():.2f}")
        st.metric("Total Profit", f"₹{sdf['profit'].sum():.2f}")
        st.dataframe(sdf, use_container_width=True)
