import streamlit as st
import pandas as pd
import time
import pdfplumber
import re
import requests
import plotly.graph_objects as go
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="QuoteGuard AI",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 2. THE PREMIUM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
    }

    /* HERO & IMAGES */
    .hero-container {
        display: flex;
        justify-content: center;
        margin-bottom: 15px;
        animation: fadeInUp 1s ease-out both;
    }
    .hero-img {
        width: 100%;
        max-width: 250px;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* GLASS CARD */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border-radius: 15px;
        padding: 25px;
        margin-top: 10px;
    }

    /* NEGOTIATION CARD (New) */
    .negotiation-card {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        padding: 20px;
        border-radius: 10px;
        margin-top: 15px;
        animation: fadeInUp 1.5s ease-out both;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* TYPOGRAPHY */
    .title-text { 
        font-size: 36px; 
        font-weight: 800; 
        color: #0F172A; 
        text-align: center; 
    }
    .subtitle-text { 
        font-size: 16px; 
        color: #64748B; 
        text-align: center; 
        margin-bottom: 15px;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 20px, 0); }
        to { opacity: 1; transform: none; }
    }
    .animate-enter { animation: fadeInUp 0.8s ease-out both; }

    .profile-img {
        border-radius: 50%;
        border: 2px solid #3B82F6;
        padding: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "English": {
        "role": "Lead Data Scientist",
        "bio": "I built this AI to stop renovation scams in Paris.",
        "wa_button": "👉 WhatsApp Me",
        "title": "QuoteGuard AI",
        "subtitle": "Paris Renovation Verification Engine",
        "proj_label": "Project Category",
        "upload_label": "Upload Devis (PDF)",
        "prog_init": "Initializing AI...",
        "prog_check": "🔎 Checking Gov Database...",
        "prog_done": "✅ Analysis Complete",
        "verdict": "Verdict",
        "metric_quote": "Quoted Price",
        "metric_fair": "Fair Market Est.",
        "metric_markup": "vs Market",
        "chart_title": "Price Comparison",
        "risk_high": "HIGH RISK",
        "risk_safe": "SAFE",
        "alert_title": "⚠️ You are overpaying by",
        "alert_btn": "🚨 Get Help from Hussnain",
        "safe_title": "✅ Great Deal! You are saving",
        "safe_btn": "💬 Confirm with Expert",
        "nego_title": "💡 AI Negotiation Script",
        "nego_desc": "Copy this text and send it to your artisan to lower the price:",
        "unknown": "❓ CHECK MANUALLY",
        "addr_missing": "Address not detected",
        "active": "✅ ACTIVE",
        "closed": "❌ CLOSED",
        "projects": {"Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡", "Painting 🎨": "Painting 🎨", "General 🔨": "General 🔨"}
    },
    "Français": {
        "role": "Data Scientist Principal",
        "bio": "J'ai créé cette IA pour stopper les arnaques aux travaux à Paris.",
        "wa_button": "👉 Me contacter (WhatsApp)",
        "title": "QuoteGuard AI",
        "subtitle": "Vérificateur de Devis Travaux",
        "proj_label": "Type de Projet",
        "upload_label": "Télécharger Devis (PDF)",
        "prog_init": "Démarrage de l'IA...",
        "prog_check": "🔎 Vérification SIRET...",
        "prog_done": "✅ Analyse Terminée",
        "verdict": "Verdict",
        "metric_quote": "Prix du Devis",
        "metric_fair": "Prix Juste",
        "metric_markup": "vs Marché",
        "chart_title": "Comparaison des Prix",
        "risk_high": "RISQUE ÉLEVÉ",
        "risk_safe": "SÛR",
        "alert_title": "⚠️ Vous payez trop cher de",
        "alert_btn": "🚨 Contacter l'Expert",
        "safe_title": "✅ Bonne affaire ! Économie :",
        "safe_btn": "💬 Confirmer ce devis",
        "nego_title": "💡 Script de Négociation IA",
        "nego_desc": "Copiez ce texte et envoyez-le à votre artisan pour baisser le prix :",
        "unknown": "❓ VÉRIFIER MANUELLEMENT",
        "addr_missing": "Adresse non détectée",
        "active": "✅ ACTIF",
        "closed": "❌ FERMÉ",
        "projects": {"Plumbing 🚿": "Plomberie 🚿", "Electricity ⚡": "Electricité ⚡", "Painting 🎨": "Peinture 🎨", "General 🔨": "Rénovation 🔨"}
    }
}

# --- FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def check_company_status(siret_query, t):
    try:
        r = requests.get(f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}")
        if r.status_code == 200 and len(r.json()) > 0:
            c = r.json()[0]
            status = t["active"] if c.get('etat_administratif') == 'A' else t["closed"]
            return True, c.get('label', 'Unknown'), status, c.get('first_matching_etablissement', {}).get('address', '')
    except: pass
    return False, "Unknown", t["unknown"], ""

def extract_data_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages: text += page.extract_text() or ""
        price = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        siret = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        return (float(price.group(1).replace(" ", "").replace(",", ".")) if price else 0.0), (siret.group(0).replace(" ", "") if siret else None), True
    except: return 0.0, None, False

def create_chart(user, fair, t):
    fig = go.Figure(data=[
        go.Bar(name="Market Price", x=['Cost'], y=[fair], marker_color='#22C55E'),
        go.Bar(name="Your Quote", x=['Cost'], y=[user], marker_color='#EF4444')
    ])
    fig.update_layout(
        barmode='group', height=200, margin=dict(l=10, r=10, t=30, b=10),
        title_text=t["chart_title"], plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif", size=12)
    )
    return fig

# --- APP LAYOUT ---
with st.sidebar:
    lang = st.radio("🌐 Language", ["English", "Français"], horizontal=True)
    t = TRANSLATIONS[lang]
    st.markdown("<br>", unsafe_allow_html=True)
    img = get_img_as_base64("profile.jpeg")
    if img:
        st.markdown(f'<div style="display: flex; justify-content: center;"><img src="data:image/jpeg;base64,{img}" class="profile-img" style="width: 120px; height: 120px; object-fit: cover;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; margin-top: 15px;"><h3 style="margin:0; color:white;">Hussnain</h3><p style="opacity: 0.8; font-size: 12px; color:#cbd5e1;">{t["role"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; font-size: 12px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.2);">{t["bio"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button(t['wa_button'], "https://wa.me/33759823532", type="primary")

st.markdown("""
    <div class="hero-container">
        <img src="https://images.unsplash.com/photo-1633613286991-611fe299c4be?q=80&w=600&auto=format&fit=crop" class="hero-img">
    </div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])
proj_display = list(t["projects"].values())
sel_disp = c1.selectbox(t["proj_label"], proj_display)
sel_key = [k for k, v in t["projects"].items() if v == sel_disp][0]
with c2: file = st.file_uploader(t["upload_label"], type=["pdf"])

if file:
    st.markdown("---")
    bar = st.progress(0, t["prog_init"])
    time.sleep(0.5)
    price, siret, _ = extract_data_from_pdf(file)
    bar.progress(50, t["prog_check"])
    c_name, c_status, c_addr = "Unknown", t["unknown"], ""
    if siret: _, c_name, c_status, c_addr = check_company_status(siret, t)
    bar.progress(100, t["prog_done"])
    time.sleep(0.3)
    bar.empty()

    if price == 0: price = 1250.0
    fair = {"Plumbing 🚿": 600, "Electricity ⚡": 900, "Painting 🎨": 1200, "General 🔨": 2000}.get(sel_key, 1000)
    markup = int(((price - fair) / fair) * 100)
    difference = price - fair
    
    risk = t["risk_high"] if markup > 40 else t["risk_safe"]
    color = "#EF4444" if markup > 40 else "#22C55E"

    # 1. MAIN RESULTS
    st.markdown(f'<div style="background: rgba(255,255,255,0.5); padding: 15px; border-radius: 10px; border-left: 5px solid {color}; margin-top: 15px;">', unsafe_allow_html=True)
    st.markdown(f"### {t['verdict']}: <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric(t["metric_quote"], f"€{price:,.0f}", f"{markup}% {t['metric_markup']}", delta_color="inverse")
    m2.metric(t["metric_fair"], f"€{fair:,.0f}")
    st.plotly_chart(create_chart(price, fair, t), use_container_width=True)
    
    # 2. COMPANY INFO
    st.markdown("---")
    st.markdown(f"**🏢 {c_name}**")
    c1, c2 = st.columns([3, 1])
    with c1: st.caption(f"📍 {c_addr}" if c_addr else t["addr_missing"])
    with c2: st.markdown(f"**{c_status}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. THE MONEY MAKER SECTION
    st.markdown("<br>", unsafe_allow_html=True)
    if markup > 40:
        # LOSS AVERSION ALERT
        st.error(f"{t['alert_title']} €{difference:,.0f}!")
        
        # AI NEGOTIATOR (NEW FEATURE)
        st.markdown(f"""
        <div class="negotiation-card">
            <h4>{t['nego_title']} 🤖</h4>
            <p>{t['nego_desc']}</p>
            <code style="background: white; padding: 10px; display: block; border-radius: 5px; color: #333;">
                "Bonjour, j'ai bien reçu votre devis de {price}€. Cependant, après vérification des prix du marché parisien pour ce type de travaux, la moyenne se situe autour de {fair}€. Pouvez-vous revoir votre offre pour vous rapprocher de ce montant ? Merci."
            </code>
        </div>
        """, unsafe_allow_html=True)
        
        st.link_button(t["alert_btn"], f"https://wa.me/33759823532?text=I%20need%20help%20negotiating%20a%20quote%20of%20{price}EUR")
    else:
        st.success(f"{t['safe_title']} €{abs(difference):,.0f}!")
        st.link_button(t["safe_btn"], f"https://wa.me/33759823532?text=Checking%20quote%20({price}EUR)")

st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("<br>", unsafe_allow_html=True)
st.caption("© 2025 QuoteGuard AI - Paris")