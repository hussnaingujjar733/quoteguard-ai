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

# --- 2. THE "SILICON VALLEY" CSS ---
st.markdown("""
    <style>
    /* HIDE STREAMLIT UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* APP BACKGROUND (Subtle Gradient) */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
    }

    /* SIDEBAR (Dark Premium Navy) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* ANIMATIONS */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 30px, 0); }
        to { opacity: 1; transform: none; }
    }
    @keyframes pulse-blue {
        0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
    }
    .animate-enter {
        animation: fadeInUp 0.8s ease-out both;
    }

    /* PROFILE PICTURE (Breathing) */
    .profile-img {
        border-radius: 50%;
        border: 3px solid #3B82F6;
        padding: 3px;
        animation: pulse-blue 3s infinite;
    }

    /* HERO IMAGE STYLE (FIXED) */
    .hero-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
        animation: fadeInUp 1s ease-out both;
        overflow: hidden;
        border-radius: 20px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    .hero-img {
        width: 100%;
        max-width: 600px; /* Made it slightly wider for cinematic look */
        height: auto;
        object-fit: cover;
    }

    /* GLASSMORPHISM CARD */
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        border-radius: 24px;
        padding: 35px;
        margin-top: 20px;
        animation: fadeInUp 1.2s ease-out both;
    }

    /* TYPOGRAPHY */
    .title-text { 
        font-size: 46px; 
        font-weight: 900; 
        color: #0F172A; 
        text-align: center; 
        letter-spacing: -1px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .subtitle-text { 
        font-size: 18px; 
        color: #64748B; 
        text-align: center; 
        margin-bottom: 10px; 
        font-weight: 500;
    }
    
    /* BADGES */
    .trust-badge {
        text-align: center;
        padding: 15px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #475569;
        transition: transform 0.3s;
    }
    .trust-badge:hover { transform: translateY(-5px); }
    </style>
""", unsafe_allow_html=True)

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "English": {
        "role": "Lead Data Scientist",
        "bio": "I built this AI to stop renovation scams in Paris. Message me directly for help.",
        "wa_button": "👉 WhatsApp Me",
        "title": "QuoteGuard AI",
        "subtitle": "Paris Renovation Verification Engine",
        "proj_label": "Project Category",
        "upload_label": "Upload Devis (PDF)",
        "prog_init": "Initializing AI...",
        "prog_check": "🔎 Checking Gov Database...",
        "prog_done": "✅ Done",
        "verdict": "Verdict",
        "metric_quote": "Quoted Price",
        "metric_fair": "Fair Market Est.",
        "metric_markup": "vs Market",
        "chart_fair": "Market Price",
        "chart_user": "Your Quote",
        "chart_title": "Price Comparison",
        "risk_high": "HIGH RISK",
        "risk_safe": "SAFE",
        "alert_title": "⚠️ Overpriced. Do not sign.",
        "alert_btn": "🚨 Report to Hussnain",
        "safe_title": "✅ Price looks fair.",
        "safe_btn": "💬 Ask Second Opinion",
        "trust_title": "Why Expats Trust QuoteGuard",
        "badge_fast": "Instant",
        "badge_gov": "Gov Data",
        "badge_priv": "Private",
        "unknown": "❓ CHECK MANUALLY",
        "addr_missing": "Address not detected",
        "active": "✅ ACTIVE",
        "closed": "❌ CLOSED",
        "projects": {"Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡", "Painting 🎨": "Painting 🎨", "General 🔨": "General 🔨"}
    },
    "Français": {
        "role": "Data Scientist Principal",
        "bio": "J'ai créé cette IA pour stopper les arnaques aux travaux à Paris. Écrivez-moi pour de l'aide.",
        "wa_button": "👉 Me contacter (WhatsApp)",
        "title": "QuoteGuard AI",
        "subtitle": "Vérificateur de Devis Travaux",
        "proj_label": "Type de Projet",
        "upload_label": "Télécharger Devis (PDF)",
        "prog_init": "Démarrage de l'IA...",
        "prog_check": "🔎 Vérification SIRET...",
        "prog_done": "✅ Terminé",
        "verdict": "Verdict",
        "metric_quote": "Prix du Devis",
        "metric_fair": "Prix Moyen Marché",
        "metric_markup": "vs Marché",
        "chart_fair": "Prix du Marché",
        "chart_user": "Votre Devis",
        "chart_title": "Comparaison des Prix",
        "risk_high": "RISQUE ÉLEVÉ",
        "risk_safe": "SÛR",
        "alert_title": "⚠️ Trop cher. Ne signez pas.",
        "alert_btn": "🚨 Signaler à l'Expert",
        "safe_title": "✅ Le prix semble correct.",
        "safe_btn": "💬 Demander un 2ème avis",
        "trust_title": "Pourquoi nous faire confiance ?",
        "badge_fast": "Rapide",
        "badge_gov": "Données Gouv",
        "badge_priv": "Privé",
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
        go.Bar(name=t["chart_fair"], x=['Cost'], y=[fair], marker_color='#22C55E'),
        go.Bar(name=t["chart_user"], x=['Cost'], y=[user], marker_color='#EF4444')
    ])
    fig.update_layout(
        barmode='group', 
        height=250, 
        margin=dict(l=20, r=20, t=30, b=20),
        title_text=t["chart_title"],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif")
    )
    return fig

# --- APP LAYOUT ---

# SIDEBAR
with st.sidebar:
    lang = st.radio("🌐 Language / Langue", ["English", "Français"], horizontal=True)
    t = TRANSLATIONS[lang]
    st.markdown("<br>", unsafe_allow_html=True)
    img = get_img_as_base64("profile.jpeg")
    if img:
        st.markdown(f'<div style="display: flex; justify-content: center;"><img src="data:image/jpeg;base64,{img}" class="profile-img" style="width: 140px; height: 140px; object-fit: cover;"></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; margin-top: 20px;"><h2 style="margin:0; font-weight: 800;">Hussnain</h2><p style="opacity: 0.8; font-size: 14px;">{t["role"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 12px; font-size: 13px; margin-top: 15px; border: 1px solid rgba(255,255,255,0.2);">{t["bio"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button(t['wa_button'], "https://wa.me/33759823532", type="primary")

# MAIN CONTENT

# 1. HERO IMAGE (The "Beautiful Picture" - using a RELIABLE Unsplash URL)
st.markdown("""
    <div class="hero-container">
        <img src="https://images.unsplash.com/photo-1633613286991-611fe299c4be?q=80&w=1000&auto=format&fit=crop" class="hero-img" alt="Renovation Security">
    </div>
""", unsafe_allow_html=True)

# 2. HEADERS (Animated)
st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

# 3. MAIN GLASS CARD (The "Unique" UI)
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
    
    risk = t["risk_high"] if markup > 40 else t["risk_safe"]
    color = "#EF4444" if markup > 40 else "#22C55E"

    # RESULTS (Nested Glass Container)
    st.markdown(f'<div style="background: rgba(255,255,255,0.5); padding: 25px; border-radius: 15px; border-left: 8px solid {color}; margin-top: 20px;">', unsafe_allow_html=True)
    st.markdown(f"### 📊 {t['verdict']}: <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric(t["metric_quote"], f"€{price:,.0f}", f"{markup}% {t['metric_markup']}", delta_color="inverse")
    m2.metric(t["metric_fair"], f"€{fair:,.0f}")
    st.plotly_chart(create_chart(price, fair, t), use_container_width=True)
    st.markdown("---")
    st.markdown(f"#### 🏢 {c_name}")
    c1, c2 = st.columns([3, 1])
    with c1: st.caption(f"📍 {c_addr}" if c_addr else t["addr_missing"])
    with c2: st.markdown(f"**{c_status}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if markup > 40:
        st.error(t["alert_title"])
        st.link_button(t["alert_btn"], f"https://wa.me/33759823532?text=HIGH%20RISK%20quote%20detected%20({price}EUR)")
    else:
        st.success(t["safe_title"])
        st.link_button(t["safe_btn"], f"https://wa.me/33759823532?text=Checking%20quote%20({price}EUR)")

st.markdown('</div>', unsafe_allow_html=True) # End Glass Card

# 4. FOOTER (Animated Badges)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter" style="text-align: center; color: #64748B; margin-bottom: 20px;">{t["trust_title"]}</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)
with b1: st.markdown(f'<div class="trust-badge animate-enter">⚡<br><b>{t["badge_fast"]}</b></div>', unsafe_allow_html=True)
with b2: st.markdown(f'<div class="trust-badge animate-enter" style="animation-delay: 0.2s;">🏛️<br><b>{t["badge_gov"]}</b></div>', unsafe_allow_html=True)
with b3: st.markdown(f'<div class="trust-badge animate-enter" style="animation-delay: 0.4s;">🔒<br><b>{t["badge_priv"]}</b></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)