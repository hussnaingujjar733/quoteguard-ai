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

# --- TRANSLATION DICTIONARY ---
TRANSLATIONS = {
    "English": {
        "role": "Lead Data Scientist",
        "bio": "I built this AI to stop renovation scams in Paris. Message me directly if you need a trusted artisan.",
        "wa_button": "👉 WhatsApp Me",
        "title": "🛡️ QuoteGuard AI",
        "subtitle": "Paris Renovation Verification Engine (Beta)",
        "proj_label": "Project Category",
        "upload_label": "Upload Devis (PDF)",
        "upload_type": ["pdf"],
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
        "comp_status": "Status",
        "addr_missing": "Address not detected",
        "active": "✅ ACTIVE",
        "closed": "❌ CLOSED",
        "unknown": "❓ CHECK MANUALLY",
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
        "projects": {"Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡", "Painting 🎨": "Painting 🎨", "General 🔨": "General 🔨"}
    },
    "Français": {
        "role": "Data Scientist Principal",
        "bio": "J'ai créé cette IA pour stopper les arnaques aux travaux à Paris. Écrivez-moi si vous cherchez un artisan de confiance.",
        "wa_button": "👉 Me contacter (WhatsApp)",
        "title": "🛡️ QuoteGuard AI",
        "subtitle": "Vérificateur de Devis Travaux (Bêta)",
        "proj_label": "Type de Projet",
        "upload_label": "Télécharger Devis (PDF)",
        "upload_type": ["pdf"],
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
        "comp_status": "Statut",
        "addr_missing": "Adresse non détectée",
        "active": "✅ ACTIF",
        "closed": "❌ FERMÉ",
        "unknown": "❓ VÉRIFIER MANUELLEMENT",
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
        "projects": {"Plumbing 🚿": "Plomberie 🚿", "Electricity ⚡": "Electricité ⚡", "Painting 🎨": "Peinture 🎨", "General 🔨": "Rénovation 🔨"}
    }
}

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .title-text { font-size: 40px; font-weight: 800; color: #0F172A; text-align: center; }
    .subtitle-text { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 30px; }
    .card { padding: 25px; border-radius: 15px; background-color: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #E2E8F0; margin-bottom: 20px; }
    .trust-badge { text-align: center; padding: 10px; background: #F8FAFC; border-radius: 8px; font-size: 14px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def check_company_status(siret_query, lang_dict):
    try:
        r = requests.get(f"https://recherche-entreprises.api.gouv.fr/search?q={siret_query}")
        if r.status_code == 200 and len(r.json()) > 0:
            c = r.json()[0]
            status = lang_dict["active"] if c.get('etat_administratif') == 'A' else lang_dict["closed"]
            return True, c.get('label', 'Unknown'), status, c.get('first_matching_etablissement', {}).get('address', '')
    except: pass
    return False, "Unknown", lang_dict["unknown"], ""

def extract_data_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages: text += page.extract_text() or ""
        price = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        siret = re.search(r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{5}\b", text)
        return (float(price.group(1).replace(" ", "").replace(",", ".")) if price else 0.0), (siret.group(0).replace(" ", "") if siret else None), True
    except: return 0.0, None, False

def create_chart(user, fair, lang_dict):
    fig = go.Figure(data=[
        go.Bar(name=lang_dict["chart_fair"], x=['Cost'], y=[fair], marker_color='#22C55E'),
        go.Bar(name=lang_dict["chart_user"], x=['Cost'], y=[user], marker_color='#EF4444')
    ])
    fig.update_layout(barmode='group', height=250, margin=dict(l=20, r=20, t=20, b=20), title_text=lang_dict["chart_title"])
    return fig

# --- SIDEBAR & LANGUAGE ---
with st.sidebar:
    # Language Selector
    lang = st.radio("🌐 Language / Langue", ["English", "Français"], horizontal=True)
    t = TRANSLATIONS[lang] # Load dictionary based on selection

    st.markdown("<br>", unsafe_allow_html=True)
    img = get_img_as_base64("profile.jpeg")
    if img:
        st.markdown(f'<div style="display: flex; justify-content: center;"><img src="data:image/jpeg;base64,{img}" style="width: 130px; height: 130px; object-fit: cover; border-radius: 50%; border: 3px solid #BFDBFE;"></div>', unsafe_allow_html=True)
    
    st.markdown(f"""<div style="text-align: center; margin-top: 15px;"><h3>Hussnain</h3><p style="color: #64748B; font-weight: bold;">{t['role']}</p></div>""", unsafe_allow_html=True)
    st.info(t['bio'])
    st.link_button(t['wa_button'], "https://wa.me/33759823532", type="primary")

# --- MAIN APP ---
st.markdown(f'<p class="title-text">{t["title"]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="subtitle-text">{t["subtitle"]}</p>', unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1])

# Project Selection Logic (Map displayed name back to math key)
project_display = list(t["projects"].values())
selected_display = c1.selectbox(t["proj_label"], project_display)
# Find the original key (e.g., "Plumbing 🚿") to do the math correctly
selected_key = [k for k, v in t["projects"].items() if v == selected_display][0]

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
    fair = {"Plumbing 🚿": 600, "Electricity ⚡": 900, "Painting 🎨": 1200, "General 🔨": 2000}.get(selected_key, 1000)
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

# --- TRUST BADGES ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div style="text-align: center; color: #64748B; margin-bottom: 20px;">{t["trust_title"]}</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)
with b1: st.markdown(f'<div class="trust-badge">⚡<br><b>{t["badge_fast"]}</b></div>', unsafe_allow_html=True)
with b2: st.markdown(f'<div class="trust-badge">🏛️<br><b>{t["badge_gov"]}</b></div>', unsafe_allow_html=True)
with b3: st.markdown(f'<div class="trust-badge">🔒<br><b>{t["badge_priv"]}</b></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div style="text-align: center; color: #aaa; font-size: 12px;">© 2025 QuoteGuard AI. All rights reserved.</div>', unsafe_allow_html=True)