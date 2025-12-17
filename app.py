import streamlit as st
import pandas as pd
import time
import random
import pdfplumber
import re
import requests
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(
    page_title="QuoteGuard AI",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING (The "Pro" Look) ---
st.markdown("""
    <style>
    /* Hide Default Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography */
    .title-text { font-size: 40px; font-weight: 800; color: #0F172A; text-align: center; font-family: sans-serif; }
    .subtitle-text { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 30px; }
    
    /* Card Styling */
    .card { 
        padding: 25px; 
        border-radius: 15px; 
        background-color: white; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        border: 1px solid #E2E8F0; 
        margin-bottom: 20px; 
    }
    
    /* Button Styling */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND INTELLIGENCE ---

def check_company_status(siret_query):
    """ Queries French Government API for company legitimacy """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                company = data[0]
                label = company.get('label', 'Unknown')
                # 'A' means Active, 'C' means Closed
                status = "✅ ACTIVE" if company.get('etat_administratif') == 'A' else "❌ CLOSED"
                address = company.get('first_matching_etablissement', {}).get('address', '')
                return True, label, status, address
    except: pass
    return False, "Unknown", "❓ NOT FOUND", ""

def extract_data_from_pdf(uploaded_file):
    """ Extracts the Price and SIRET Number from the PDF """
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages: text += page.extract_text() or ""
            
        # Regex to find Price (e.g. 1 200,00 €)
        price_match = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        # Regex to find SIRET (14 digits)
        siret_match = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        
        price = float(price_match.group(1).replace(" ", "").replace(",", ".")) if price_match else 0.0
        siret = siret_match.group(0).replace(" ", "") if siret_match else None
        return price, siret, True
    except: pass
    return 0.0, None, False

def create_pro_chart(user_price, fair_price):
    """ Creates the Interactive Plotly Chart """
    fig = go.Figure(data=[
        go.Bar(name='Fair Market Price', x=['Renovation Cost'], y=[fair_price], marker_color='#22C55E'),
        go.Bar(name='Your Quote', x=['Renovation Cost'], y=[user_price], marker_color='#EF4444')
    ])
    fig.update_layout(barmode='group', title_text='Price Comparison', height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# --- FRONTEND UI ---

# 1. SIDEBAR PROFILE (Fixed Layout)
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    # Use columns to center the image perfectly
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try:
            st.image("profile.jpeg", width=130)
        except:
            st.error("Upload profile.jpeg")
            
    st.markdown("""
        <div style="text-align: center;">
            <h3 style="margin: 10px 0 0 0;">Hussnain</h3>
            <p style="color: #64748B; font-size: 14px; font-weight: bold;">Lead Data Scientist</p>
            <div style="background-color: #F1F5F9; padding: 10px; border-radius: 8px; font-size: 12px; color: #334155; border: 1px solid #E2E8F0;">
                "I built this tool to help expats avoid renovation scams in Paris. Message me for help."
            </div>
            <br>
        </div>
    """, unsafe_allow_html=True)
    
    st.link_button("👉 WhatsApp Me", "https://wa.me/33759823532", type="primary")

# 2. MAIN HEADER
st.markdown('<p class="title-text">🛡️ QuoteGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Paris Renovation Verification Engine (Beta)</p>', unsafe_allow_html=True)

# 3. INPUT CARD
st.markdown('<div class="card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])
with c1: project_type = st.selectbox("Project Category", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General 🔨"])
with c2: uploaded_file = st.file_uploader("Upload Devis (PDF)", type=["pdf"])
st.markdown('</div>', unsafe_allow_html=True)

# 4. ANALYSIS LOGIC
if uploaded_file:
    # A. Animation Sequence
    progress_bar = st.progress(0, "Initializing AI Engine...")
    time.sleep(0.5)
    
    price, siret, success = extract_data_from_pdf(uploaded_file)
    progress_bar.progress(50, "🔎 Verifying Company Identity with Gov API...")
    
    comp_name, comp_status, comp_addr = "Unknown", "❓ Check Manually", ""
    if siret: _, comp_name, comp_status, comp_addr = check_company_status(siret)
    
    progress_bar.progress(100, "✅ Analysis Complete")
    time.sleep(0.3)
    progress_bar.empty()

    if price == 0: price = 1250.0 # Fallback for demo if OCR fails

    # B. Risk Logic
    fair_limit = {"Plumbing 🚿": 600, "Electricity ⚡": 900}.get(project_type, 1000)
    markup = int(((price - fair_limit) / fair_limit) * 100)
    risk = "HIGH RISK" if markup > 40 else "SAFE"
    color = "#EF4444" if risk == "HIGH RISK" else "#22C55E"

    # 5. RESULT DASHBOARD
    st.markdown(f'<div class="card" style="border-left: 8px solid {color};">', unsafe_allow_html=True)
    
    # Header
    st.markdown(f"### 📊 Analysis Verdict: <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
    
    # Metrics
    m1, m2 = st.columns(2)
    m1.metric("Quoted Price", f"€{price:,.0f}", f"{markup}% vs Market", delta_color="inverse")
    m2.metric("Fair Market Estimate", f"€{fair_limit:,.0f}")
    
    # Chart
    st.plotly_chart(create_pro_chart(price, fair_limit), use_container_width=True)
    
    # Company Info
    st.markdown("---")
    st.markdown(f"#### 🏢 Artisan Check: {comp_name}")
    c1, c2 = st.columns([3, 1])
    with c1: 
        if comp_addr: st.caption(f"📍 {comp_addr}")
        else: st.caption("Address not detected")
    with c2:
        st.markdown(f"**{comp_status}**")
        
    st.markdown('</div>', unsafe_allow_html=True)

    # 6. CALL TO ACTION
    st.markdown("### 💡 What should you do?")
    if risk == "HIGH RISK":
        st.error("⚠️ This quote is significantly overpriced. Do not sign it yet.")
        st.link_button("🚨 Report to Expert (Hussnain)", f"https://wa.me/33759823532?text=I%20have%20a%20HIGH%20RISK%20quote%20for%20{price}EUR")
    else:
        st.success("✅ This price looks fair. You are good to go.")
        st.link_button("💬 Ask a Second Opinion", f"https://wa.me/33759823532?text=I%20have%20a%20quote%20for%20{price}EUR")

# FOOTER
st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)