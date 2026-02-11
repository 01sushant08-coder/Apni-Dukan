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

# --- 2. CSS FOR VISIBILITY ---
# We are forcing labels to be dark and bold so they are always visible
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    
    /* Force all labels to be Black and Bold */
    label, .stMarkdown, p, .stSelectbox p, .stTextInput p {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        opacity: 1 !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #2e5a27 !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* Header Styling */
    h1, h2, h3 { color: #2e5a27 !important; text-align: center; }
    
    /* Button Styling */
    .stButton>button {
        background-color: #e67e22 !important;
        color: white !important;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DB CONNECTION ---
URL = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
KEY = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
db = create_client(URL, KEY)

# --- 4. DATA HELPERS ---
TOWERS = [chr(i) for i in range(ord('A'), ord('M'))]
FLATS = [f"{floor}{flat:02d}" for floor in range(1, 19) for flat in range(1, 5)]

# --- 5. NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

if st.sidebar.button("🏠 Back to Home"):
    st.session_state.page = "🏠 Home"
    st.rerun()

# --- SECTION: HOME DASHBOARD ---
if st.session_state.page == "🏠 Home":
    st.title("🌿 Apni Dukan")
    st.subheader("What would you like to do?")
    
    if st.button("📦 Inventory Manager", use_container_width=True):
        st.session_state.page = "📦 Inventory Manager"; st.rerun()
        
    if st.button("📢 Marketing", use_container_width=True):
        st.session_state.page = "📢 Marketing"; st.rerun()
        
    if st.button("📝 Billing", use_container_width=True):
        st.session_state.page = "📝 Billing"; st.rerun()
        
    if st.button("📊 Daily Reports", use_container_width=True):
        st.session_state.page = "📊 Daily Reports"; st.rerun()

# --- SECTION: INVENTORY ---
elif st.session_state.page == "📦 Inventory Manager":
    st.header("📦 Inventory Manager")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    with st.expander("⚙️ Add New Item to Master List"):
        new_item = st.text_input("New Item Name (e.g. Avocado)")
        if st.button("Add Now"):
            if new_item:
                db.table("master_list").upsert({"name": new_item}).execute()
                st.success(f"{new_item} added!")
                st.rerun()

    try:
        m_res = db.table("master_list").select("*").execute()
        m_opts = sorted([i['name'] for i in m_res.data]) if m_res.data else ["Potato"]
    except: m_opts = ["Potato"]

    with st.form("inv_form", clear_on_submit=True):
        st.write("### Update Current Stock")
        p_name = st.selectbox("Select Product", m_opts)
        c_p = st.number_input("Cost Price (Buy)", min_value=0.0)
        s_p = st.number_input("Sale Price (Sell)", min_value=0.0)
        flash = st.checkbox("Include in Flash Sale?")
        if st.form_submit_button("Update Inventory"):
            db.table("inventory").upsert({"name": p_name, "cost_price": c_p, "sale_price": s_p, "is_flash_sale": flash}).execute()
            st.success("Updated!")

# --- SECTION: MARKETING ---
elif st.session_state.page == "📢 Marketing":
    st.header("📢 WhatsApp Marketing")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        msg_type = st.radio("Choose Message Type:", ["Daily Price List", "Flash Sale"], horizontal=True)
        
        if msg_type == "Daily Price List":
            if st.button("Generate Daily Price List"):
                msg = f"*🏪 Apni Dukan - Fresh Arrivals*\n"
                for _, row in df.sort_values("name").iterrows():
                    msg += f"• {row['name']}: *₹{row['sale_price']}*\n"
                st.link_button("🚀 Share to Group", f"https://wa.me/?text={urllib.parse.quote(msg)}")
        else:
            flash_df = df[df["is_flash_sale"] == True]
            if not flash_df.empty:
                if st.button("Generate Flash Blast"):
                    msg = "⚡ *FLASH SALE* ⚡\n"
                    for _, row in flash_df.iterrows():
                        msg += f"🔥 *{row['name']}* @ *₹{row['sale_price']}*!\n"
                    st.link_button("🚀 Send Flash Blast", f"https://wa.me/?text={urllib.parse.quote(msg)}")
            else:
                st.info("No items marked for Flash Sale.")

# --- SECTION: BILLING ---
elif st.session_state.page == "📝 Billing":
    st.header("📝 Create New Bill")
    if st.button("⬅️ Back to Menu"): st.session_state.page = "🏠 Home"; st.rerun()
    
    res = db.table("inventory").select("*").execute()
    if res.data:
        df_inv = pd.DataFrame(res.data)
        with st.form("bill_form", clear_on_submit=True):
            name = st.text_input("Step 1: Customer Name")
            tow = st.selectbox("Step 2: Select Tower", TOWERS)
            flt = st.selectbox("Step 3: Select Flat", FLATS)
            itm = st.selectbox("Step 4: Select Item", df_inv["name"].tolist())
            unt = st.selectbox("Step 5: Select Unit", ["kg", "gms", "Dozen", "Piece"])
            qty = st.number_input("Step 6: Enter Quantity", min_value=0.1)
            
            if st.form_submit_button("Finalize & Generate Bill"):
                row = df_inv[df_inv["name"] == itm].iloc[0]
                c_qty = qty/1000 if unt == "gms" else qty
                tot = round(row["sale_price"] * c_qty, 2)
                prof = round((row["sale_price"] - row["cost_price"]) * c_qty, 2)
                
                db.table("sales").insert({"item_name": itm, "qty": f"{qty} {unt}", "total_bill": tot, "profit": prof, "tower_flat": f"T-{tow} {flt}"}).execute()
                
                msg = f"*Apni Dukan Receipt*\n*Cust:* {name}\n*Loc:* T-{tow} {flt}\n*Item:* {itm}\n*Qty:* {qty}{unt}\n*Total: ₹{tot}*"
                st.link_button("📲 Click to Send WhatsApp", f"https://wa.me/?text={urllib.parse.quote(msg)}")
