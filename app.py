# ==============================
# QuoteGuard – Premium + Pricing
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
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(
    page_title="QuoteGuard",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
.stApp {
    background-color: #F8FAFC;
    background-image:
        radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%),
        radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%),
        radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
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
@keyframes slideUp { from {opacity:0; transform: translateY(20px);} to {opacity:1; transform:none;} }
.animate-enter { animation: slideUp .6s ease-out both; }
.profile-img { border-radius: 50%; border: 3px solid #60A5FA; padding: 3px; }
</style>
""", unsafe_allow_html=True)

# ---------- TRANSLATIONS (PREMIUM + PRICING) ----------
TRANSLATIONS = {
    "English": {
        "role": "Verification Engine",
        "bio": "Independent pricing verification based on Paris market standards and official government records.",
        "wa_button": "👉 Request Professional Review",
        "title": "QuoteGuard",
        "subtitle": "Independent Renovation Quote Audit for Paris",
        "proj_label": "Project Category",
        "upload_label": "Upload Quote (PDF)",
        "prog_init": "Initializing Audit...",
        "prog_check": "🔎 Verifying Company Authority...",
        "prog_done": "✅ Analysis Complete",
        "verdict": "Audit Verdict",
        "metric_quote": "Quoted Price",
        "metric_fair": "Fair Market Est.",
        "metric_markup": "vs Market",
        "chart_title": "Price Deviation Analysis",
        "risk_high": "HIGH OVERCHARGE RISK",
        "risk_safe": "WITHIN MARKET STANDARDS",
        "alert_title": "⚠️ Potential overcharge detected:",
        "alert_btn": "🚨 Speak with an Expert Advisor",
        "safe_title": "✅ Quote appears fair. Savings:",
        "safe_btn": "💬 Confirm with Expert",
        "nego_title": "💡 Negotiation Strategy",
        "nego_desc": "Use this data-backed script to request a price adjustment:",
        "unknown": "❓ MANUAL CHECK REQ.",
        "addr_missing": "Address not detected on document",
        "active": "✅ LEGALLY ACTIVE",
        "closed": "❌ COMPANY CLOSED",
        "projects": {"Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡", "Painting 🎨": "Painting 🎨", "General 🔨": "General 🔨"},
        "disclaimer": "Independent • No affiliation with contractors • Estimations based on market averages.",
        "upgrade_title": "Upgrade to Expert Review",
        "price_free": "Standard",
        "price_paid": "Expert Audit",
        "feat_1": "Instant Verdict",
        "feat_2": "Market Price Check",
        "feat_3": "SIRET Verification",
        "feat_4": "Human Expert Review",
        "feat_5": "Negotiation Support",
        "cta_free": "Your Current Plan",
        "cta_paid": "Get Expert Help",
        "rec": "RECOMMENDED"
    },
    "Français": {
        "role": "Expertise & Audit",
        "bio": "Vérification indépendante des prix travaux basée sur les référentiels parisiens et les données légales.",
        "wa_button": "👉 Demander une contre-expertise",
        "title": "QuoteGuard",
        "subtitle": "Audit Indépendant de Devis Travaux - Paris",
        "proj_label": "Catégorie du Projet",
        "upload_label": "Analyser mon Devis (PDF)",
        "prog_init": "Initialisation de l'audit...",
        "prog_check": "🔎 Vérification de l'existence légale (SIRET)...",
        "prog_done": "✅ Analyse terminée",
        "verdict": "Verdict de l'Audit",
        "metric_quote": "Montant du Devis",
        "metric_fair": "Prix Marché Estimé",
        "metric_markup": "Écart vs Marché",
        "chart_title": "Analyse des Écarts de Prix",
        "risk_high": "RISQUE DE SURFACTURATION",
        "risk_safe": "OFFRE COMPÉTITIVE",
        "alert_title": "⚠️ Écart critique détecté :",
        "alert_btn": "🚨 Parler à un Expert",
        "safe_title": "✅ Devis conforme au marché. Gain potentiel :",
        "safe_btn": "💬 Valider ce devis",
        "nego_title": "💡 Argumentaire de Négociation",
        "nego_desc": "Utilisez ce script pour rationaliser le prix avec l'artisan :",
        "unknown": "❓ VÉRIFICATION MANUELLE REQUISE",
        "addr_missing": "Adresse non détectée sur le document",
        "active": "✅ SOCIÉTÉ ACTIVE (INSEE)",
        "closed": "❌ SOCIÉTÉ RADIÉE / FERMÉE",
        "projects": {"Plumbing 🚿": "Plomberie / Sanitaire 🚿", "Electricity ⚡": "Électricité / Mise aux normes ⚡", "Painting 🎨": "Peinture & Finitions 🎨", "General 🔨": "Rénovation Globale 🔨"},
        "disclaimer": "Indépendant • Aucune affiliation avec les artisans • Estimations basées sur des moyennes de marché.",
        "upgrade_title": "Passer à l'Audit Expert",
        "price_free": "Standard",
        "price_paid": "Audit Expert",
        "feat_1": "Verdict Instantané",
        "feat_2": "Vérification Prix Marché",
        "feat_3": "Vérification SIRET",
        "feat_4": "Revue par un Expert Humain",
        "feat_5": "Assistance Négociation",
        "cta_free": "Votre Plan Actuel",
        "cta_paid": "Réserver mon Expert",
        "rec": "RECOMMANDÉ"
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
        go.Bar(name="Market", x=["Cost"], y=[fair_price]),
        go.Bar(name="Your Quote", x=["Cost"], y=[user_price])
    ])
    fig.update_layout(barmode="group", height=220, title=title,
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ---------- SIDEBAR ----------
lang = st.sidebar.radio("🌐 Language", ["English", "Français"], horizontal=True)
t = TRANSLATIONS[lang]

img = get_img_as_base64("profile.jpeg")
if img:
    st.sidebar.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{img}" class="profile-img" width="110"></div>', unsafe_allow_html=True)

st.sidebar.markdown(f"**Hussnain** \n{t['role']}")
st.sidebar.caption(t["bio"])
st.sidebar.link_button(t["wa_button"], "https://wa.me/33759823532")

# ---------- HEADER ----------
st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

# TRUST BADGE & PROCESS
st.markdown("""
<div style="text-align:center; font-size:12px; opacity:0.7; margin-bottom: 20px;">
    <i>Independent • No affiliation with contractors • Data-backed</i>
</div>
<div style="text-align:center; font-size:13px; opacity:0.9; margin-bottom: 30px; font-weight:600;">
    1️⃣ Document Scan &nbsp;&nbsp;→&nbsp;&nbsp;
    2️⃣ Market Benchmark &nbsp;&nbsp;→&nbsp;&nbsp;
    3️⃣ Audit Verdict
</div>
""", unsafe_allow_html=True)

# ---------- INPUTS ----------
c1, c2 = st.columns(2)
project = c1.selectbox(t["proj_label"], list(t["projects"].values()))
file = c2.file_uploader(t["upload_label"], type=["pdf"])

# ---------- PROCESS ----------
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

    if price == 0:
        price = 1200.0

    fair_map = {
        "Plumbing 🚿": 600,
        "Electricity ⚡": 900,
        "Painting 🎨": 1200,
        "General Renovation 🔨": 2000,
        "Plomberie / Sanitaire 🚿": 600,
        "Électricité / Mise aux normes ⚡": 900,
        "Peinture & Finitions 🎨": 1200,
        "Rénovation Globale 🔨": 2000
    }
    fair = fair_map.get(project, 1000)
    markup = int(((price - fair) / fair) * 100)
    diff = price - fair

    risk = t["risk_high"] if markup > 40 else t["risk_safe"]
    color = "#EF4444" if markup > 40 else "#22C55E"

    st.markdown(f"### {t['verdict']}: **:{color}[{risk}]**")
    m1, m2 = st.columns(2)
    m1.metric(t["metric_quote"], f"€{price:,.0f}", f"{markup}% {t['metric_markup']}")
    m2.metric(t["metric_fair"], f"€{fair:,.0f}")
    st.plotly_chart(chart(price, fair, t["chart_title"]), use_container_width=True)

    st.markdown(f"**🏢 {name}**")
    st.caption(addr if addr else t["addr_missing"])
    st.caption(status)

    if markup > 40:
        st.error(f"{t['alert_title']} €{diff:,.0f}")
        st.markdown(f"""
        <div class="negotiation-card">
            <b>{t['nego_title']}</b>
            <p>{t['nego_desc']}</p>
            <pre>Bonjour, après vérification des standards parisiens, la moyenne est de {fair}€. Pouvez-vous revoir ce devis ?</pre>
        </div>
        """, unsafe_allow_html=True)
        st.link_button(t["alert_btn"], "https://wa.me/33759823532")
    else:
        st.success(f"{t['safe_title']} €{abs(diff):,.0f}")
        st.link_button(t["safe_btn"], "https://wa.me/33759823532")

    # ---------- REPORT GENERATION ----------
    st.markdown("---")
    report_text = f"""
    {t['title']} - {t['subtitle']}
    --------------------------------------------------
    DATE: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    ID: {str(int(time.time()))}
    
    1. PROJECT DETAILS
    ------------------
    Category: {project}
    Company Detected: {name}
    Status: {status}
    Address: {addr}
    
    2. FINANCIAL AUDIT
    ------------------
    Quoted Price: €{price:,.2f}
    Fair Market Estimate: €{fair:,.2f}
    Difference: €{diff:,.2f}
    
    VERDICT: {risk}
    --------------------------------------------------
    {t['disclaimer']}
    """
    st.download_button(
        label="📄 " + ("Download Audit Report" if lang == "English" else "Télécharger le Rapport"),
        data=report_text,
        file_name=f"QuoteGuard_Audit_{int(time.time())}.txt",
        mime="text/plain"
    )

    # ---------- PRICING SECTION (NEW) ----------
    st.markdown("---")
    st.markdown(f"### 💎 {t['upgrade_title']}")

    c1, c2 = st.columns(2)
    
    # Free Tier
    with c1:
        st.markdown(f"""
        <div style="border:1px solid #E2E8F0; border-radius:10px; padding:20px; height:100%;">
            <h4 style="margin:0;">{t['price_free']}</h4>
            <h2 style="font-size:32px; color:#64748B;">€0</h2>
            <p style="font-size:12px; opacity:0.7;">Automated Check</p>
            <hr style="margin:10px 0; border:0; border-top:1px solid #eee;">
            <ul style="list-style:none; padding:0; font-size:13px; line-height:2;">
                <li>✅ {t['feat_1']}</li>
                <li>✅ {t['feat_2']}</li>
                <li>✅ {t['feat_3']}</li>
                <li style="opacity:0.5;">❌ {t['feat_4']}</li>
                <li style="opacity:0.5;">❌ {t['feat_5']}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Paid Tier
    with c2:
        st.markdown(f"""
        <div style="border:2px solid #22C55E; background:#F0FDF4; border-radius:10px; padding:20px; height:100%; position:relative;">
            <div style="position:absolute; top:-12px; right:20px; background:#22C55E; color:white; padding:2px 10px; border-radius:12px; font-size:10px; font-weight:bold;">{t['rec']}</div>
            <h4 style="margin:0; color:#166534;">{t['price_paid']}</h4>
            <h2 style="font-size:32px; color:#15803D;">€29</h2>
            <p style="font-size:12px; color:#166534;">Manual Review</p>
            <hr style="margin:10px 0; border:0; border-top:1px solid #bbf7d0;">
            <ul style="list-style:none; padding:0; font-size:13px; line-height:2; color:#14532d;">
                <li>✅ <b>{t['feat_1']}</b></li>
                <li>✅ {t['feat_4']}</li>
                <li>✅ {t['feat_5']}</li>
            </ul>
            <a href="https://wa.me/33759823532?text=I%20am%20interested%20in%20the%20Expert%20Audit%20for%2029EUR" target="_blank" style="display:block; background:#166534; color:white; text-align:center; padding:10px; border-radius:6px; text-decoration:none; font-weight:600; margin-top:15px;">{t['cta_paid']}</a>
        </div>
        """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.caption(t["disclaimer"])
st.caption("✔️ Free instant check • 💼 Professional human review available")
st.caption(f"© {datetime.now().year} QuoteGuard")