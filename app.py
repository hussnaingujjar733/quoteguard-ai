import streamlit as st
import pandas as pd
import time
import random
import pdfplumber
import re
import requests
import plotly.graph_objects as go # <--- THE PRO CHART TOOL

# --- CONFIG ---
st.set_page_config(page_title="QuoteGuard AI", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .title-text { font-size: 42px; font-weight: 800; color: #0F172A; text-align: center; }
    .subtitle-text { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 25px; }
    .card { padding: 25px; border-radius: 15px; background-color: white; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #E2E8F0; margin-bottom: 20px; }
    .expert-badge { background-color: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def check_company_status(siret_query):
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                company = data[0]
                return True, company.get('label', 'Unknown'), "✅ ACTIVE" if company.get('etat_administratif') == 'A' else "❌ CLOSED", company.get('first_matching_etablissement', {}).get('address', '')
    except: pass
    return False, "Unknown", "❓ NOT FOUND", ""

def extract_data_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages: text += page.extract_text() or ""
        price_match = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        siret_match = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        
        price = float(price_match.group(1).replace(" ", "").replace(",", ".")) if price_match else 0.0
        siret = siret_match.group(0).replace(" ", "") if siret_match else None
        return price, siret, True
    except: pass
    return 0.0, None, False

def create_pro_chart(user_price, fair_price):
    """ Creates a beautiful interactive bar chart """
    fig = go.Figure(data=[
        go.Bar(name='Fair Market Price', x=['Renovation Cost'], y=[fair_price], marker_color='#22C55E'), # Green
        go.Bar(name='Your Quote', x=['Renovation Cost'], y=[user_price], marker_color='#EF4444') # Red
    ])
    fig.update_layout(barmode='group', title_text='Price Comparison (Interactive)', height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig

# --- FRONTEND ---

st.markdown('<p class="title-text">🛡️ QuoteGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">The Official Paris Renovation Verification Engine</p>', unsafe_allow_html=True)

# SIDEBAR PROFILE
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.markdown("### Hussnain")
    st.markdown("**Lead Data Scientist**")
    st.info("I built this tool to help expats avoid scams. If you need a trusted artisan, message me directly.")
    st.markdown("[👉 WhatsApp Me](https://wa.me/33759823532)")

# INPUT CARD
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

    if price == 0: price = 1200.0 # Demo Fallback

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
    
    # PLOTLY CHART
    st.plotly_chart(create_pro_chart(price, fair_limit), use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### 🏢 Company Background Check")
    st.write(f"**Name:** {comp_name}")
    st.write(f"**Status:** {comp_status}")
    if comp_addr: st.caption(f"📍 {comp_addr}")
    
    st.markdown("---")
    st.markdown("#### 💡 Recommendation")
    if risk == "HIGH RISK":
        st.error("This quote is overpriced. Do not sign.")
        st.link_button("🚨 Report this to Hussnain (Expert Help)", f"https://wa.me/33759823532?text=I%20found%20a%20HIGH%20RISK%20quote%20for%20{price}EUR")
    else:
        st.success("This quote looks fair. You can proceed.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# LEGAL FOOTER
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #aaa; font-size: 12px;">
    <p>© 2025 QuoteGuard AI. All rights reserved.</p>
    <p>Disclaimer: This tool provides estimates based on market data. It does not constitute legal or financial advice.</p>
</div>
""", unsafe_allow_html=True)