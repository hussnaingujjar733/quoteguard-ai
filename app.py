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
    initial_sidebar_state="expanded" # This forces it open
)

# --- 2. THE DESIGNER CSS (FIXED) ---
st.markdown("""
    <style>
    /* 1. Remove the "Streamlit" branding but KEEP the sidebar button */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;}  <-- I DELETED THIS LINE SO YOU CAN SEE THE ARROW */

    /* 2. APP BACKGROUND (The "Pro" Grey Look) */
    .stApp {
        background-color: #F1F5F9; /* Light SaaS Grey */
    }

    /* 3. SIDEBAR STYLE */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        color: white !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
        color: #E2E8F0 !important;
    }

    /* 4. PROFILE ANIMATION */
    @keyframes breathe {
        0% { transform: scale(1); box-shadow: 0 0 0px rgba(59, 130, 246, 0.0); }
        50% { transform: scale(1.03); box-shadow: 0 0 15px rgba(59, 130, 246, 0.5); }
        100% { transform: scale(1); box-shadow: 0 0 0px rgba(59, 130, 246, 0.0); }
    }
    .profile-img {
        border-radius: 50%;
        border: 2px solid #3B82F6;
        animation: breathe 3s infinite ease-in-out;
        transition: all 0.3s ease;
    }

    /* 5. MAIN CARD (White on Grey) */
    .card {
        padding: 40px;
        border-radius: 20px;
        background-color: white;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border: 1px solid #E2E8F0;
        margin-bottom: 25px;
    }

    /* 6. TYPOGRAPHY */
    .title-text { 
        font-size: 50px; 
        font-weight: 900; 
        color: #0F172A; 
        text-align: center; 
        font-family: 'Arial Black', sans-serif; 
        margin-bottom: 0px;
    }
    .subtitle-text { 
        font-size: 20px; 
        color: #64748B; 
        text-align: center; 
        margin-bottom: 40px; 
        font-weight: 500;
    }
    
    /* 7. BADGES */
    .trust-badge {
        text-align: center;
        padding: 15px;
        background: white;
        border-radius: 12px;
        font-size: 14px;
        border: 1px solid #E2E8F0;
        color: #475569;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- TRANSLATIONS (Same as before) ---
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
        paper_bgcolor='rgba(0,0,0,0)'
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
    st.markdown(f'<div style="text-align: center; margin-top: 20px;"><h2 style="color: white; margin:0;">Hussnain</h2><p style="color: #94A3B8; font-size: 14px;">{t["role"]}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; font-size: 13px; color: #E2E8F0; margin-top: 15px;">{t["bio"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button(t['wa_button'], "https://wa.me/33759823532", type="primary")

# MAIN CONTENT
st.markdown(f'<p class="title-text">🛡️ {t["title"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle-text">{t["subtitle"]}</p>', unsafe_allow_html=True)

# INPUT CARD
st.markdown('<div class="card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])
proj_display = list(t["projects"].values())
sel_disp = c1.selectbox(t["proj_label"], proj_display)
sel_key = [k for k, v in t["projects"].items() if v == sel_disp][0]
with c2: file = st.file_uploader(t["upload_label"], type=["pdf"])
st.markdown('</div>', unsafe_allow_html=True)

if file:
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

    st.markdown(f'<div class="card" style="border-left: 8px solid {color};">', unsafe_allow_html=True)
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

    if markup > 40:
        st.error(t["alert_title"])
        st.link_button(t["alert_btn"], f"https://wa.me/33759823532?text=HIGH%20RISK%20quote%20detected%20({price}EUR)")
    else:
        st.success(t["safe_title"])
        st.link_button(t["safe_btn"], f"https://wa.me/33759823532?text=Checking%20quote%20({price}EUR)")

# TRUST BADGES
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div style="text-align: center; color: #64748B; margin-bottom: 20px;">{t["trust_title"]}</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)
with b1: st.markdown(f'<div class="trust-badge">⚡<br><b>{t["badge_fast"]}</b></div>', unsafe_allow_html=True)
with b2: st.markdown(f'<div class="trust-badge">🏛️<br><b>{t["badge_gov"]}</b></div>', unsafe_allow_html=True)
with b3: st.markdown(f'<div class="trust-badge">🔒<br><b>{t["badge_priv"]}</b></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)