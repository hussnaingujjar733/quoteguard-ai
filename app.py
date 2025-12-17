# ==============================
# QuoteGuard – National Edition (France)
# ==============================
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import time
import pdfplumber
import re
import requests
import plotly.graph_objects as go
import base64
import random
from datetime import datetime
from fpdf import FPDF

# ---------- CONFIG ----------
st.set_page_config(
    page_title="QuoteGuard France",
    page_icon="🇫🇷",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---------- SESSION STATE (For Demo Mode) ----------
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

def activate_demo():
    st.session_state.demo_mode = True

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
.stApp {
    background-color: #F8FAFC;
    background-image:
        radial-gradient(at 0% 0%, hsla(215,28%,17%,1) 0, transparent 50%),
        radial-gradient(at 50% 0%, hsla(210,29%,24%,1) 0, transparent 50%),
        radial-gradient(at 100% 0%, hsla(220,30%,20%,1) 0, transparent 50%);
    background-attachment: fixed;
}
.negotiation-card {
    background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    border: 1px solid #86EFAC; padding: 20px; border-radius: 12px; margin-top: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }
.title-text { font-size: 42px; font-weight: 800; color: #FFFFFF; text-align: center; }
.subtitle-text { font-size: 16px; color: #CBD5E1; text-align: center; margin-bottom: 40px; }
.live-badge {
    background-color: #EF4444; color: white; padding: 4px 8px; border-radius: 4px;
    font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ---------- REGIONAL PRICING MULTIPLIERS ----------
# Paris is the baseline (1.0). Other cities are cheaper.
REGIONS = {
    "Paris & Île-de-France": 1.0,
    "Lyon / Rhône-Alpes": 0.90,
    "Nice / Côte d'Azur": 0.95,
    "Bordeaux / Gironde": 0.85,
    "Marseille / PACA": 0.85,
    "Lille / Nord": 0.80,
    "Toulouse / Occitanie": 0.80,
    "Rest of France (Rural)": 0.70
}

# ---------- TRANSLATIONS ----------
TRANSLATIONS = {
    "English": {
        "role": "National Verification Engine",
        "bio": "Independent pricing verification for all regions of France.",
        "wa_button": "👉 Request Expert Review",
        "title": "QuoteGuard",
        "subtitle": "National Renovation Audit & Price Check 🇫🇷",
        "loc_label": "📍 Region / City",
        "proj_label": "Project Category",
        "upload_label": "Upload Quote (PDF)",
        "prog_init": "Initializing Audit...",
        "prog_check": "🔎 Verifying Company Authority...",
        "prog_done": "✅ Analysis Complete",
        "verdict": "Audit Verdict",
        "metric_quote": "Quoted Price",
        "metric_fair": "Fair Regional Est.",
        "metric_markup": "vs Regional Avg",
        "chart_title": "Regional Price Analysis",
        "risk_high": "HIGH OVERCHARGE RISK",
        "risk_safe": "WITHIN REGIONAL STANDARDS",
        "alert_title": "⚠️ Potential overcharge detected:",
        "alert_btn": "🚨 Speak with an Expert Advisor",
        "safe_title": "✅ Quote appears fair. Savings:",
        "safe_btn": "💬 Confirm with Expert",
        "nego_title": "💡 Negotiation Strategy",
        "nego_desc": "Use this data-backed script to request a price adjustment:",
        "unknown": "❓ MANUAL CHECK REQ.",
        "addr_missing": "Address not detected",
        "active": "✅ LEGALLY ACTIVE",
        "closed": "❌ COMPANY CLOSED",
        "projects": {"Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡", "Painting 🎨": "Painting 🎨", "General 🔨": "General 🔨"},
        "disclaimer": "Independent • No affiliation with contractors • Estimations based on regional averages.",
        "upgrade_title": "Upgrade to Expert Review",
        "price_free": "Standard",
        "price_paid": "Expert Audit",
        "feat_1": "Instant Verdict",
        "feat_2": "Regional Price Check",
        "feat_3": "SIRET Verification",
        "feat_4": "Human Expert Review",
        "feat_5": "Negotiation Support",
        "cta_free": "Your Current Plan",
        "cta_paid": "Get Expert Help",
        "rec": "RECOMMENDED",
        "demo_btn": "⚡ Try Demo Quote",
        "live_update": "LIVE MARKET: Inflation +2.1% (Materials)"
    },
    "Français": {
        "role": "Expertise & Audit National",
        "bio": "Vérification indépendante des prix travaux pour toute la France.",
        "wa_button": "👉 Demander une contre-expertise",
        "title": "QuoteGuard",
        "subtitle": "Audit National de Devis Travaux 🇫🇷",
        "loc_label": "📍 Région / Ville",
        "proj_label": "Catégorie du Projet",
        "upload_label": "Analyser mon Devis (PDF)",
        "prog_init": "Initialisation de l'audit...",
        "prog_check": "🔎 Vérification de l'existence légale (SIRET)...",
        "prog_done": "✅ Analyse terminée",
        "verdict": "Verdict de l'Audit",
        "metric_quote": "Montant du Devis",
        "metric_fair": "Prix Régional Estimé",
        "metric_markup": "Écart vs Région",
        "chart_title": "Analyse des Prix Régionaux",
        "risk_high": "RISQUE DE SURFACTURATION",
        "risk_safe": "OFFRE COMPÉTITIVE",
        "alert_title": "⚠️ Écart critique détecté :",
        "alert_btn": "🚨 Parler à un Expert",
        "safe_title": "✅ Devis conforme au marché. Gain potentiel :",
        "safe_btn": "💬 Valider ce devis",
        "nego_title": "💡 Argumentaire de Négociation",
        "nego_desc": "Utilisez ce script pour rationaliser le prix avec l'artisan :",
        "unknown": "❓ VÉRIFICATION MANUELLE REQUISE",
        "addr_missing": "Adresse non détectée",
        "active": "✅ SOCIÉTÉ ACTIVE (INSEE)",
        "closed": "❌ SOCIÉTÉ RADIÉE / FERMÉE",
        "projects": {"Plumbing 🚿": "Plomberie / Sanitaire 🚿", "Electricity ⚡": "Électricité / Mise aux normes ⚡", "Painting 🎨": "Peinture & Finitions 🎨", "General 🔨": "Rénovation Globale 🔨"},
        "disclaimer": "Indépendant • Aucune affiliation avec les artisans • Estimations basées sur des moyennes régionales.",
        "upgrade_title": "Passer à l'Audit Expert",
        "price_free": "Standard",
        "price_paid": "Audit Expert",
        "feat_1": "Verdict Instantané",
        "feat_2": "Vérification Prix Régional",
        "feat_3": "Vérification SIRET",
        "feat_4": "Revue par un Expert Humain",
        "feat_5": "Assistance Négociation",
        "cta_free": "Votre Plan Actuel",
        "cta_paid": "Réserver mon Expert",
        "rec": "RECOMMANDÉ",
        "demo_btn": "⚡ Essayer la Démo",
        "live_update": "MARCHÉ EN DIRECT : Inflation Matériaux +2,1%"
    }
}

# ---------- HELPERS ----------
def get_img_as_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

def extract_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for p in pdf.pages:
            text += p.extract_text() or ""
    price = re.search(r"(Total|Montant).*?(\d+[\s\d]*[\.,]\d{2})", text, re.I)
    siret = re.search(r"\b\d{14}\b", text.replace(" ", ""))
    amount = float(price.group(2).replace(" ", "").replace(",", ".")) if price else 0.0
    return amount, (siret.group(0) if siret else None)

def check_siret(siret):
    try:
        r = requests.get(f"https://recherche-entreprises.api.gouv.fr/search?q={siret}", timeout=10)
        if r.status_code == 200 and r.json():
            c = r.json()[0]
            status = "ACTIVE" if c.get("etat_administratif") == "A" else "CLOSED"
            addr = c.get("first_matching_etablissement", {}).get("address", "")
            return c.get("label", "Unknown"), status, addr
    except Exception:
        pass
    return "Unknown", "CHECK", ""

def chart(user_price, fair_price, title):
    fig = go.Figure([
        go.Bar(name="Market Avg", x=["Cost"], y=[fair_price], marker_color='#22C55E'),
        go.Bar(name="Your Quote", x=["Cost"], y=[user_price], marker_color='#EF4444')
    ])
    fig.update_layout(barmode="group", height=220, title=title,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ---------- UPDATED PDF GENERATOR (WITH REGION) ----------
def create_pdf(t, project, region, name, status, addr, price, fair, diff, risk):
    def clean_text(text):
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("€", "EUR").replace("•", "-").replace("’", "'").replace("…", "...")
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, clean_text(t["title"]), ln=True, align="C")
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, clean_text(t["subtitle"]), ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Details
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"DATE: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, clean_text(f"Region: {region}"), ln=True)
    pdf.cell(0, 10, clean_text(f"Category: {project}"), ln=True)
    pdf.cell(0, 10, clean_text(f"Company: {name} ({status})"), ln=True)
    pdf.ln(5)
    
    # Financials
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "FINANCIAL ANALYSIS", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, clean_text(t["metric_quote"]), border=1)
    pdf.cell(0, 10, f"{price:,.2f} EUR", border=1, ln=True)
    pdf.cell(100, 10, clean_text(t["metric_fair"]), border=1)
    pdf.cell(0, 10, f"{fair:,.2f} EUR", border=1, ln=True)
    pdf.cell(100, 10, "Difference", border=1)
    pdf.cell(0, 10, f"{diff:,.2f} EUR", border=1, ln=True)
    pdf.ln(5)
    
    # Verdict
    if "HIGH" in risk or "RISQUE" in risk:
        pdf.set_text_color(200, 50, 50)
    else:
        pdf.set_text_color(50, 150, 50)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"VERDICT: {risk}"), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, clean_text(t["disclaimer"]))
    
    return pdf.output(dest="S").encode("latin-1")

# ---------- SIDEBAR ----------
lang = st.sidebar.radio("🌐 Language", ["English", "Français"], horizontal=True)
t = TRANSLATIONS[lang]

img = get_img_as_base64("profile.jpeg")
if img:
    st.sidebar.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{img}" class="profile-img" width="110"></div>', unsafe_allow_html=True)

st.sidebar.markdown(f"**Hussnain** \n{t['role']}")
st.sidebar.caption(t["bio"])
st.sidebar.link_button(t["wa_button"], "https://wa.me/33759823532")

# ---------- HEADER (LIVE UPDATES) ----------
st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

# LIVE MARKET BADGE
st.markdown(f"""
<div style="text-align:center; margin-bottom:25px;">
    <span class="live-badge">🔴 {t['live_update']}</span>
</div>
""", unsafe_allow_html=True)

# TRUST BADGE
st.markdown("""
<div style="text-align:center; font-size:13px; opacity:0.9; margin-bottom: 30px; font-weight:600;">
    1️⃣ Select Region &nbsp;&nbsp;→&nbsp;&nbsp;
    2️⃣ Upload Quote &nbsp;&nbsp;→&nbsp;&nbsp;
    3️⃣ Audit Verdict
</div>
""", unsafe_allow_html=True)

# ---------- INPUTS (WITH REGION FILTER) ----------
c1, c2 = st.columns(2)
# NEW: Region Selector
region = c1.selectbox(t["loc_label"], list(REGIONS.keys()))
# Project Selector
project = c2.selectbox(t["proj_label"], list(t["projects"].values()))

# File Upload
file = st.file_uploader(t["upload_label"], type=["pdf"])

# ---------- LOGIC ----------
if file or st.session_state.demo_mode:
    
    if file:
        bar = st.progress(0, t["prog_init"])
        time.sleep(0.4)
        price, siret = extract_from_pdf(file)
        bar.progress(50, t["prog_check"])
        name, status, addr = ("Unknown", t["unknown"], "")
        if siret:
            name, status, addr = check_siret(siret)
        bar.progress(100, t["prog_done"])
        time.sleep(0.2)
        bar.empty()
    else:
        st.info("⚡ DEMO MODE: Simulating Quote...")
        time.sleep(1.0)
        price = 25000.0
        name = "Renov' National Expert SAS"
        status = t["active"]
        addr = f"Zone Industrielle, {region.split('/')[0]}"

    if price == 0: price = 1500.0

    # DYNAMIC PRICING LOGIC
    # 1. Base prices (Paris baseline)
    fair_map_base = {
        "Plumbing 🚿": 600, "Electricity ⚡": 900, "Painting 🎨": 1200, "General 🔨": 2000,
        "Plomberie / Sanitaire 🚿": 600, "Électricité / Mise aux normes ⚡": 900,
        "Peinture & Finitions 🎨": 1200, "Rénovation Globale 🔨": 18000
    }
    
    # 2. Apply Regional Multiplier
    base_price = fair_map_base.get(project, 1000)
    multiplier = REGIONS[region]
    fair = base_price * multiplier

    # Demo adjustment
    if st.session_state.demo_mode and "General" in str(project) or "Globale" in str(project):
         fair = 18000 * multiplier

    markup = int(((price - fair) / fair) * 100)
    diff = price - fair
    risk = t["risk_high"] if markup > 40 else t["risk_safe"]
    color = "#EF4444" if markup > 40 else "#22C55E"

    # RESULTS
    st.markdown(f"### {t['verdict']}: **:{color}[{risk}]**")
    m1, m2 = st.columns(2)
    m1.metric(t["metric_quote"], f"€{price:,.0f}", f"{markup}% {t['metric_markup']}")
    m2.metric(t["metric_fair"], f"€{fair:,.0f}", f"{region.split('/')[0]} Avg")
    st.plotly_chart(chart(price, fair, t["chart_title"]), use_container_width=True)

    st.markdown(f"**🏢 {name}**")
    st.caption(status)

    if markup > 40:
        st.error(f"{t['alert_title']} €{diff:,.0f}")
        st.markdown(f"""
        <div class="negotiation-card">
            <b>{t['nego_title']}</b>
            <p>{t['nego_desc']}</p>
            <pre>Bonjour, le prix moyen pour {project} à {region.split('/')[0]} est de {fair:,.0f}€. Pouvez-vous revoir votre offre ?</pre>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success(f"{t['safe_title']} €{abs(diff):,.0f}")

    # PDF REPORT
    st.markdown("---")
    pdf_data = create_pdf(t, project, region, name, status, addr, price, fair, diff, risk)
    st.download_button(
        label="📄 " + ("Download PDF Audit" if lang == "English" else "Télécharger Audit PDF"),
        data=pdf_data,
        file_name=f"QuoteGuard_{region.split('/')[0]}_{int(time.time())}.pdf",
        mime="application/pdf"
    )

    if st.session_state.demo_mode:
        if st.button("🔄 Reset"):
            st.session_state.demo_mode = False
            st.rerun()

else:
    # LANDING PAGE
    st.markdown("<br>", unsafe_allow_html=True)
    c_demo = st.container()
    col_d1, col_d2, col_d3 = c_demo.columns([1, 2, 1])
    with col_d2:
        if st.button(t["demo_btn"], type="primary", use_container_width=True):
            activate_demo()
            st.rerun()
    
    st.markdown("---")
    st.markdown(f"### ⚡ {('How it works' if lang == 'English' else 'Comment ça marche')}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("1. Select Region")
    with c2:
        st.info("2. Upload PDF")
    with c3:
        st.info("3. Get Audit")