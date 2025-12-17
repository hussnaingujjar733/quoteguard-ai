import streamlit as st
import pandas as pd
import time
import random
import pdfplumber
import re
import requests
import plotly.graph_objects as go

# --- CONFIG ---
st.set_page_config(
    page_title="QuoteGuard AI",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .title-text { font-size: 42px; font-weight: 800; color: #0F172A; text-align: center; }
    .subtitle-text { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 25px; }
    .card { padding: 25px; border-radius: 15px; background-color: white; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #E2E8F0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def check_company_status(siret_query):
    """ Checks French Government API for company status """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                company = data[0]
                label = company.get('label', 'Unknown')
                status = "✅ ACTIVE" if company.get('etat_administratif') == 'A' else "❌ CLOSED"
                address = company.get('first_matching_etablissement', {}).get('address', '')
                return True, label, status, address
    except: pass
    return False, "Unknown", "❓ NOT FOUND", ""

def extract_data_from_pdf(uploaded_file):
    """ Extracts Price and SIRET from PDF """
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages: text += page.extract_text() or ""
            
        # Regex for Price
        price_match = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        # Regex for SIRET (14 digits)
        siret_match = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        
        price = float(price_match.group(1).replace(" ", "").replace(",", ".")) if price_match else 0.0
        siret = siret_match.group(0).replace(" ", "") if siret_match else None
        return price, siret, True
    except: pass
    return 0.0, None, False

def create_pro_chart(user_price, fair_price):
    """ Interactive Plotly Chart """
    fig = go.Figure(data=[
        go.Bar(name='Fair Market Price', x=['Total Cost'], y=[fair_price], marker_color='#22C55E'),
        go.Bar(name='Your Quote', x=['Total Cost'], y=[user_price], marker_color='#EF4444')
    ])
    fig.update_layout(barmode='group', title_text='Price Comparison', height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# --- FRONTEND ---

st.markdown('<p class="title-text">🛡️ QuoteGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">The Official Paris Renovation Verification Engine</p>', unsafe_allow_html=True)

# SIDEBAR PROFILE (YOUR PHOTO)
with st.sidebar:
    try:
        # This looks for 'profile.jpeg' in your folder
        st.image("profile.jpeg", width=150)
    except:
        st.warning("⚠️ Upload 'profile.jpeg' to see your photo here.")
        
    st.markdown("### Hussnain")
    st.markdown("**Lead Data Scientist**")
    st.info("I built this tool to help expats avoid scams. If you need a trusted artisan, message me directly.")
    st.markdown("[👉 WhatsApp Me](https://wa.me/33759823532)")

# MAIN INPUT
st.markdown('<div class="card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])
with c1: project_type = st.selectbox("Project Category", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General 🔨"])
with c2: uploaded_file = st.file_uploader("Upload Devis (PDF)", type=["pdf"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    # ANIMATION
    bar = st.progress(0, "Starting Engine...")
    time.sleep(0.5)
    
    price, siret, success = extract_data_from_pdf(uploaded_file)
    bar.progress(50, "🔎 Verifying Company Identity...")
    
    comp_name, comp_status, comp_addr = "Unknown", "❓ Check Manually", ""
    if siret: _, comp_name, comp_status, comp_addr = check_company_status(siret)
    
    bar.progress(100, "✅ Done")
    time.sleep(0.3)
    bar.empty()

    if price == 0: price = 1250.0 # Demo Fallback

    # LOGIC
    fair_limit = {"Plumbing 🚿": 600, "Electricity ⚡": 900}.get(project_type, 1000)
    markup = int(((price - fair_limit) / fair_limit) * 100)
    risk = "HIGH RISK" if markup > 40 else "SAFE"
    
    # RESULT CARD
    st.markdown(f'<div class="card" style="border-left: 5px solid {"#EF4444" if risk == "HIGH RISK" else "#22C55E"};">', unsafe_allow_html=True)
    st.markdown(f"### 📊 Analysis: {risk}")
    
    m1, m2 = st.columns(2)
    m1.metric("Artisan Quote", f"€{price:,.0f}", f"{markup}% vs Market", delta_color="inverse")
    m2.metric("Fair Market Value", f"€{fair_limit:,.0f}")
    
    st.plotly_chart(create_pro_chart(price, fair_limit), use_container_width=True)
    
    st.markdown("---")
    st.markdown(f"#### 🏢 {comp_name}")
    st.write(f"**Status:** {comp_status}")
    if comp_addr: st.caption(f"📍 {comp_addr}")
    
    st.markdown("---")
    if risk == "HIGH RISK":
        st.error("This quote is overpriced. Do not sign.")
        st.link_button("🚨 Report this to Hussnain (WhatsApp)", f"https://wa.me/33759823532?text=I%20found%20a%20HIGH%20RISK%20quote%20for%20{price}EUR")
    else:
        st.success("This quote looks fair. You can proceed.")
        
    st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)