# ==============================
# QuoteGuard AI – Complete App
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
    page_title="QuoteGuard AI",
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

# ---------- TRANSLATIONS ----------
TRANSLATIONS = {
    "English": {
        "role": "Lead Data Scientist",
        "bio": "I built this tool to help people avoid renovation scams in Paris.",
        "wa_button": "👉 WhatsApp Me",
        "title": "QuoteGuard AI",
        "subtitle": "Paris Renovation Quote Verification",
        "proj_label": "Project Category",
        "upload_label": "Upload Quote (PDF)",
        "prog_init": "Initializing analysis…",
        "prog_check": "🔎 Checking company status…",
        "prog_done": "✅ Analysis complete",
        "verdict": "Verdict",
        "metric_quote": "Quoted Price",
        "metric_fair": "Fair Estimate",
        "metric_markup": "vs Market",
        "chart_title": "Price Comparison",
        "risk_high": "HIGH RISK",
        "risk_safe": "SAFE",
        "alert_title": "⚠️ Possible overpayment of",
        "alert_btn": "🚨 Get Expert Help",
        "safe_title": "✅ Looks good! Estimated saving",
        "safe_btn": "💬 Confirm with Expert",
        "nego_title": "💡 AI Negotiation Script",
        "nego_desc": "Copy and send this to your artisan:",
        "unknown": "CHECK MANUALLY",
        "addr_missing": "Address not detected",
        "active": "ACTIVE",
        "closed": "CLOSED",
        "disclaimer": "Estimates only. This tool does not replace a professional audit.",
        "projects": {
            "Plumbing 🚿": "Plumbing 🚿",
            "Electricity ⚡": "Electricity ⚡",
            "Painting 🎨": "Painting 🎨",
            "General 🔨": "General Renovation 🔨"
        }
    },
    "Français": {
        "role": "Data Scientist Principal",
        "bio": "Outil créé pour éviter les arnaques aux devis à Paris.",
        "wa_button": "👉 Me contacter (WhatsApp)",
        "title": "QuoteGuard AI",
        "subtitle": "Vérification intelligente des devis",
        "proj_label": "Type de projet",
        "upload_label": "Télécharger le devis (PDF)",
        "prog_init": "Initialisation de l’analyse…",
        "prog_check": "🔎 Vérification de l’entreprise…",
        "prog_done": "✅ Analyse terminée",
        "verdict": "Verdict",
        "metric_quote": "Prix du devis",
        "metric_fair": "Estimation juste",
        "metric_markup": "vs marché",
        "chart_title": "Comparaison des prix",
        "risk_high": "RISQUE ÉLEVÉ",
        "risk_safe": "SÛR",
        "alert_title": "⚠️ Surcoût estimé de",
        "alert_btn": "🚨 Contacter un expert",
        "safe_title": "✅ Bonne affaire ! Économie",
        "safe_btn": "💬 Confirmer le devis",
        "nego_title": "💡 Script de négociation IA",
        "nego_desc": "Copiez et envoyez à votre artisan :",
        "unknown": "VÉRIFIER",
        "addr_missing": "Adresse non détectée",
        "active": "ACTIF",
        "closed": "FERMÉ",
        "disclaimer": "Estimations uniquement. Ne remplace pas un audit professionnel.",
        "projects": {
            "Plumbing 🚿": "Plomberie 🚿",
            "Electricity ⚡": "Électricité ⚡",
            "Painting 🎨": "Peinture 🎨",
            "General 🔨": "Rénovation générale 🔨"
        }
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

st.sidebar.markdown(f"**Hussnain**  \n{t['role']}")
st.sidebar.caption(t["bio"])
st.sidebar.link_button(t["wa_button"], "https://wa.me/33759823532")

# ---------- HEADER ----------
st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)

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
        "Plomberie 🚿": 600,
        "Électricité ⚡": 900,
        "Peinture 🎨": 1200,
        "Rénovation générale 🔨": 2000
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

# ---------- FOOTER ----------
st.caption(t["disclaimer"])
st.caption(f"© {datetime.now().year} QuoteGuard AI")
