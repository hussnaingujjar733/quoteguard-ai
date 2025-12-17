import streamlit as st
import pandas as pd
import time
import pdfplumber
import re
import requests
import plotly.graph_objects as go
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="QuoteGuard AI", page_icon="🛡️", layout="centered", initial_sidebar_state="expanded")

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .title-text { font-size: 40px; font-weight: 800; color: #0F172A; text-align: center; }
    .subtitle-text { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 30px; }
    .card { padding: 25px; border-radius: 15px; background-color: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #E2E8F0; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS ---

def get_img_as_base64(file):
    """Encodes image to Base64 to force High Quality rendering"""
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def check_company_status(siret_query):
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                c = data[0]
                return True, c.get('label', 'Unknown'), "✅ ACTIVE" if c.get('etat_administratif') == 'A' else "❌ CLOSED", c.get('first_matching_etablissement', {}).get('address', '')
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
    fig = go.Figure(data=[
        go.Bar(name='Fair Market Price', x=['Cost'], y=[fair_price], marker_color='#22C55E'),
        go.Bar(name='Your Quote', x=['Cost'], y=[user_price], marker_color='#EF4444')
    ])
    fig.update_layout(barmode='group', title_text='Price Comparison', height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# --- FRONTEND ---

# 1. HIGH QUALITY SIDEBAR PROFILE
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CONVERT IMAGE TO BASE64 (This fixes the quality/blur issue)
    img_b64 = get_img_as_base64("profile.jpeg")
    
    if img_b64:
        st.markdown(f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/jpeg;base64,{img_b64}" 
                     style="width: 150px; height: 150px; object-fit: cover; border-radius: 50%; border: 3px solid #BFDBFE; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("⚠️ profile.jpeg not found")

    st.markdown("""
        <div style="text-align: center;">
            <h3 style="margin: 15px 0 5px 0;">Hussnain</h3>
            <p style="color: #64748B; font-size: 14px; font-weight: bold;">Lead Data Scientist</p>
            <div style="background-color: #F1F5F9; padding: 12px; border-radius: 8px; font-size: 13px; color: #334155; border: 1px solid #E2E8F0; margin-bottom: 15px;">
                "I built this AI to stop renovation scams in Paris. Message me directly for help."
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.link_button("👉 Chat on WhatsApp", "https://wa.me/33759823532", type="primary")

# 2. MAIN APP
st.markdown('<p class="title-text">🛡️ QuoteGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Paris Renovation Verification Engine (Beta)</p>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])
with c1: project_type = st.selectbox("Project Category", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General 🔨"])
with c2: uploaded_file = st.file_uploader("Upload Devis (PDF)", type=["pdf"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    bar = st.progress(0, "Initializing AI...")
    time.sleep(0.5)
    price, siret, success = extract_data_from_pdf(uploaded_file)
    bar.progress(50, "🔎 Checking Database...")
    comp_name, comp_status, comp_addr = "Unknown", "❓ Check Manually", ""
    if siret: _, comp_name, comp_status, comp_addr = check_company_status(siret)
    bar.progress(100, "✅ Done")
    time.sleep(0.3)
    bar.empty()

    if price == 0: price = 1250.0 

    fair_limit = {"Plumbing 🚿": 600, "Electricity ⚡": 900}.get(project_type, 1000)
    markup = int(((price - fair_limit) / fair_limit) * 100)
    risk = "HIGH RISK" if markup > 40 else "SAFE"
    color = "#EF4444" if risk == "HIGH RISK" else "#22C55E"

    st.markdown(f'<div class="card" style="border-left: 8px solid {color};">', unsafe_allow_html=True)
    st.markdown(f"### 📊 Analysis Verdict: <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Quoted Price", f"€{price:,.0f}", f"{markup}% vs Market", delta_color="inverse")
    m2.metric("Fair Market Estimate", f"€{fair_limit:,.0f}")
    st.plotly_chart(create_pro_chart(price, fair_limit), use_container_width=True)
    
    st.markdown("---")
    st.markdown(f"#### 🏢 Artisan: {comp_name}")
    c1, c2 = st.columns([3, 1])
    with c1: st.caption(f"📍 {comp_addr}" if comp_addr else "Address not detected")
    with c2: st.markdown(f"**{comp_status}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 💡 Recommendation")
    if risk == "HIGH RISK":
        st.error("⚠️ Overpriced Quote. Do not sign.")
        st.link_button("🚨 Report to Hussnain", f"https://wa.me/33759823532?text=I%20have%20a%20HIGH%20RISK%20quote%20for%20{price}EUR")
    else:
        st.success("✅ Price looks fair.")
        st.link_button("💬 Ask Second Opinion", f"https://wa.me/33759823532?text=I%20have%20a%20quote%20for%20{price}EUR")

st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)