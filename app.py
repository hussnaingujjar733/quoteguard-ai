# ==============================
# QuoteGuard – Analytics Dashboard Edition (FIXED)
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
from fpdf import FPDF
from PIL import Image
import pytesseract
import urllib.parse

# ---------- CONFIG ----------
st.set_page_config(
    page_title="QuoteGuard France",
    page_icon="🇫🇷",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ---------- SESSION STATE ----------
if 'history' not in st.session_state:
    st.session_state.history = []
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

def activate_demo():
    st.session_state.demo_mode = True

def add_to_history(project, price, score):
    st.session_state.history.insert(0, {"time": datetime.now().strftime("%H:%M"), "project": project, "price": price, "score": score})
    st.session_state.history = st.session_state.history[:5]

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
.history-item {
    background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin-bottom: 8px; font-size: 12px;
}
.item-tag {
    background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# ---------- REGIONS & TRANSLATIONS ----------
REGIONS = {
    "Paris & Île-de-France": 1.0,
    "Lyon / Rhône-Alpes": 0.90,
    "Nice / Côte d'Azur": 0.95,
    "Bordeaux / Gironde": 0.85,
    "Marseille / PACA": 0.85,
    "Lille / Nord": 0.80,
    "Rest of France (Rural)": 0.70
}

TRANSLATIONS = {
    "English": {
        "role": "National Verification Engine",
        "bio": "Independent pricing verification using Smart Keyword Detection.",
        "wa_button": "👉 Contact Expert",
        "title": "QuoteGuard",
        "subtitle": "Smart Renovation Audit & Price Check 🇫🇷",
        "loc_label": "📍 Region / City",
        "proj_label": "Project Category",
        "upload_label": "Upload Quote (PDF, JPG, PNG)",
        "prog_init": "Reading Document...",
        "prog_check": "🔎 Detecting Items (OCR)...",
        "prog_done": "✅ Smart Analysis Complete",
        "verdict": "Trust Score",
        "metric_quote": "Quoted Price",
        "metric_fair": "Smart Estimate",
        "metric_markup": "vs Estimate",  # ADDED MISSING KEY
        "chart_title": "Fairness Gauge",
        "risk_high": "HIGH RISK",
        "risk_safe": "FAIR PRICE",
        "alert_title": "⚠️ Potential overcharge detected:",
        "alert_btn": "🚨 Speak with an Expert",
        "safe_title": "✅ Excellent Price! You are saving money.",
        "safe_btn": "💬 Confirm with Expert",
        "nego_title": "💡 Negotiation Strategy",
        "nego_desc": "We found these items in your quote. Use this logic:",
        "unknown": "❓ MANUAL CHECK REQ.",
        "addr_missing": "Address not detected",
        "active": "✅ LEGALLY ACTIVE",
        "closed": "❌ COMPANY CLOSED",
        "projects": {"General 🔨": "General 🔨", "Plumbing 🚿": "Plumbing 🚿", "Electricity ⚡": "Electricity ⚡"},
        "disclaimer": "Estimates based on detected keywords and regional averages.",
        "upgrade_title": "Upgrade to Expert Review",
        "price_free": "Standard",
        "price_paid": "Expert Audit",
        "feat_1": "AI Item Detection",
        "feat_2": "Regional Price Check",
        "feat_4": "Human Expert Review",
        "feat_5": "Negotiation Support",
        "cta_free": "Current Plan",
        "cta_paid": "Buy Audit - €29",
        "rec": "RECOMMENDED",
        "demo_btn": "⚡ Try Demo Quote",
        "live_update": "LIVE MARKET: Inflation +2.1%",
        "hist_title": "🕒 Recent Scans",
        "email_btn": "📧 Email Report",
        "feedback": "Was this helpful?",
        "stripe_url": "https://buy.stripe.com/test_12345",
        "detected_items": "🔍 AI Detected Items:",
        "match_title": "👷 Need a better price?",
        "match_btn": "Get 3 Verified Quotes"
    },
    "Français": {
        "role": "Expertise & Audit National",
        "bio": "Vérification intelligente des prix via détection de mots-clés.",
        "wa_button": "👉 Contacter Expert",
        "title": "QuoteGuard",
        "subtitle": "Audit Intelligent de Devis Travaux 🇫🇷",
        "loc_label": "📍 Région / Ville",
        "proj_label": "Catégorie du Projet",
        "upload_label": "Analyser Devis (PDF, JPG, PNG)",
        "prog_init": "Lecture du document...",
        "prog_check": "🔎 Détection des travaux (OCR)...",
        "prog_done": "✅ Analyse Intelligente Terminée",
        "verdict": "Score de Confiance",
        "metric_quote": "Montant du Devis",
        "metric_fair": "Estimation Intelligente",
        "metric_markup": "Écart vs Est.",  # ADDED MISSING KEY
        "chart_title": "Jauge de Confiance",
        "risk_high": "RISQUE ÉLEVÉ",
        "risk_safe": "PRIX CORRECT",
        "alert_title": "⚠️ Écart critique détecté :",
        "alert_btn": "🚨 Parler à un Expert",
        "safe_title": "✅ Excellent Prix ! Vous économisez.",
        "safe_btn": "💬 Valider ce devis",
        "nego_title": "💡 Stratégie de Négociation",
        "nego_desc": "Voici les éléments détectés. Utilisez cet argumentaire :",
        "unknown": "❓ VÉRIFICATION MANUELLE",
        "addr_missing": "Adresse non détectée",
        "active": "✅ SOCIÉTÉ ACTIVE (INSEE)",
        "closed": "❌ SOCIÉTÉ RADIÉE / FERMÉE",
        "projects": {"General 🔨": "Rénovation Globale 🔨", "Plumbing 🚿": "Plomberie 🚿", "Electricity ⚡": "Électricité ⚡"},
        "disclaimer": "Estimations basées sur les mots-clés détectés et moyennes régionales.",
        "upgrade_title": "Passer à l'Audit Expert",
        "price_free": "Standard",
        "price_paid": "Audit Expert",
        "feat_1": "Détection IA des Travaux",
        "feat_2": "Vérification Prix Régional",
        "feat_4": "Revue par un Expert Humain",
        "feat_5": "Assistance Négociation",
        "cta_free": "Plan Actuel",
        "cta_paid": "Acheter Audit - 29€",
        "rec": "RECOMMANDÉ",
        "demo_btn": "⚡ Essayer la Démo",
        "live_update": "MARCHÉ EN DIRECT : Inflation +2,1%",
        "hist_title": "🕒 Historique Récent",
        "email_btn": "📧 Envoyer par Email",
        "feedback": "Cet audit a-t-il été utile ?",
        "stripe_url": "https://buy.stripe.com/test_12345",
        "detected_items": "🔍 Travaux Détectés par l'IA :",
        "match_title": "👷 Besoin d'un meilleur prix ?",
        "match_btn": "Recevoir 3 Devis Vérifiés"
    }
}

# ---------- HELPERS ----------
def get_img_as_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

def extract_data(file):
    text = ""
    try:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                for p in pdf.pages:
                    text += p.extract_text() or ""
        else:
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
            
        price = re.search(r"(Total|Montant|TTC).*?(\d+[\s\d]*[\.,]\d{2})", text, re.I)
        siret = re.search(r"\b\d{14}\b", text.replace(" ", ""))
        amount = float(price.group(2).replace(" ", "").replace(",", ".")) if price else 0.0
        
        return amount, (siret.group(0) if siret else None), text
    except Exception as e:
        return 0.0, None, ""

def calculate_smart_fair_price(text, region_multiplier):
    text = text.lower()
    items_found = []
    running_total = 0
    keywords = {
        "wc": {"cost": 800, "name": "Toilette / WC"},
        "toilet": {"cost": 800, "name": "Toilette / WC"},
        "lavabo": {"cost": 600, "name": "Lavabo / Sink"},
        "douche": {"cost": 1500, "name": "Douche / Shower"},
        "baignoire": {"cost": 1800, "name": "Baignoire / Bath"},
        "chauffe-eau": {"cost": 1200, "name": "Chauffe-eau / Heater"},
        "peinture": {"cost": 2000, "name": "Forfait Peinture"},
        "carrelage": {"cost": 1500, "name": "Carrelage / Tiling"},
        "tableau": {"cost": 1500, "name": "Tableau Élec / Panel"},
        "cuisine": {"cost": 4000, "name": "Cuisine / Kitchen"},
        "fenêtre": {"cost": 1000, "name": "Fenêtre / Window"},
        "porte": {"cost": 800, "name": "Porte / Door"}
    }
    for key, data in keywords.items():
        if key in text and data['name'] not in [i['name'] for i in items_found]:
            local_cost = data['cost'] * region_multiplier
            items_found.append({"name": data['name'], "cost": local_cost})
            running_total += local_cost

    if running_total == 0:
        running_total = 1500 * region_multiplier
        items_found.append({"name": "Estimation Standard", "cost": running_total})
        
    return running_total, items_found

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

# ---------- NEW: GAUGE CHART ----------
def create_gauge(score, title):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#3b82f6"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ef4444'},
                {'range': [50, 75], 'color': '#f59e0b'},
                {'range': [75, 100], 'color': '#22c55e'}],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score}}))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# ---------- NEW: DONUT CHART ----------
def create_donut(items, labor_est):
    labels = [i['name'] for i in items] + ["Main d'oeuvre (Est.)"]
    values = [i['cost'] for i in items] + [labor_est]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return fig

def create_pdf(t, project, region, name, status, addr, price, fair, diff, risk, items):
    def clean_text(text):
        if not isinstance(text, str): text = str(text)
        text = text.replace("€", "EUR").replace("•", "-").replace("’", "'").replace("…", "...")
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, clean_text(t["title"]), ln=True, align="C")
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, clean_text(t["subtitle"]), ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"DATE: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, clean_text(f"Region: {region}"), ln=True)
    pdf.cell(0, 10, clean_text(f"Company: {name} ({status})"), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "DETECTED ITEMS:", ln=True)
    pdf.set_font("Arial", "", 10)
    for i in items:
        pdf.cell(0, 6, clean_text(f"- {i['name']}: {i['cost']:.0f} EUR"), ln=True)
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "FINANCIAL ANALYSIS", ln=True, fill=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(100, 10, clean_text(t["metric_quote"]), border=1)
    pdf.cell(0, 10, f"{price:,.2f} EUR", border=1, ln=True)
    pdf.cell(100, 10, clean_text(t["metric_fair"]), border=1)
    pdf.cell(0, 10, f"{fair:,.2f} EUR", border=1, ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, clean_text(f"VERDICT: {risk}"), ln=True, align="C")
    
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, clean_text(t["disclaimer"]))
    return pdf.output(dest="S").encode("latin-1")

# ---------- SIDEBAR ----------
lang = st.sidebar.radio("🌐 Language", ["English", "Français"], horizontal=True)
t = TRANSLATIONS[lang]
img = get_img_as_base64("profile.jpeg")
if img: st.sidebar.markdown(f'<div style="text-align:center"><img src="data:image/jpeg;base64,{img}" class="profile-img" width="110"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f"**Hussnain** \n{t['role']}")
st.sidebar.caption(t["bio"])
st.sidebar.link_button(t["wa_button"], "https://wa.me/33759823532")

# HISTORY
if len(st.session_state.history) > 0:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{t['hist_title']}**")
    for item in st.session_state.history:
        color = "🔴" if item['score'] < 50 else "🟢"
        st.sidebar.markdown(f"""<div class="history-item">{color} <b>{item['price']:,.0f}€</b> (Score: {item['score']})<br><span style="opacity:0.7">{item['time']}</span></div>""", unsafe_allow_html=True)

# ---------- MAIN UI ----------
st.markdown(f'<div class="animate-enter"><p class="title-text">🛡️ {t["title"]}</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="animate-enter"><p class="subtitle-text">{t["subtitle"]}</p></div>', unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; margin-bottom:25px;"><span class="live-badge">🔴 {t['live_update']}</span></div>""", unsafe_allow_html=True)

c1, c2 = st.columns(2)
region = c1.selectbox(t["loc_label"], list(REGIONS.keys()))
project = c2.selectbox(t["proj_label"], list(t["projects"].values()))
file = st.file_uploader(t["upload_label"], type=["pdf", "jpg", "jpeg", "png"])

# ---------- LOGIC ----------
if file or st.session_state.demo_mode:
    if file:
        bar = st.progress(0, t["prog_init"])
        time.sleep(0.4)
        price, siret, full_text = extract_data(file)
        bar.progress(50, t["prog_check"])
        name, status, addr = ("Unknown", t["unknown"], "")
        if siret: name, status, addr = check_siret(siret)
        bar.progress(100, t["prog_done"])
        time.sleep(0.2)
        bar.empty()
    else:
        st.info("⚡ DEMO MODE: Simulating Quote...")
        time.sleep(1.0)
        price = 18500.0
        full_text = "Devis: Peinture, Cuisine, Electricité, Salle de Bain (Douche, Lavabo, WC)"
        name = "Renov' Smart SAS"
        status = t["active"]
        addr = "Paris"

    if price == 0: price = 1500.0
    
    multiplier = REGIONS[region]
    fair, detected_items = calculate_smart_fair_price(full_text, multiplier)

    # Calculate Trust Score (0-100)
    diff = price - fair
    markup = int(((price - fair) / fair) * 100)
    score = max(0, min(100, 100 - markup))
    
    risk = t["risk_high"] if score < 60 else t["risk_safe"]
    
    if not st.session_state.demo_mode: add_to_history(project, price, score)

    # 1. SCORE DASHBOARD
    g1, g2 = st.columns([1.5, 1])
    with g1:
        st.plotly_chart(create_gauge(score, t["verdict"]), use_container_width=True)
    with g2:
        st.metric(t["metric_quote"], f"€{price:,.0f}", f"{markup}% {t['metric_markup']}", delta_color="inverse")
        st.metric(t["metric_fair"], f"€{fair:,.0f}", "Smart Estimate")
    
    # 2. SUCCESS CONFETTI
    if score >= 75:
        st.balloons()
        st.success(f"{t['safe_title']} €{abs(diff):,.0f}!")
    else:
        st.error(f"{t['alert_title']} €{diff:,.0f}")
        
    # 3. DETECTED ITEMS & DONUT
    st.markdown("---")
    c_list, c_chart = st.columns(2)
    with c_list:
        st.markdown(f"**{t['detected_items']}**")
        for item in detected_items:
            st.markdown(f"• {item['name']} (~{item['cost']:.0f}€)")
    with c_chart:
         st.plotly_chart(create_donut(detected_items, fair*0.3), use_container_width=True)

    st.markdown(f"**🏢 {name}**")
    st.caption(status)

    # 4. LEAD GEN (If Score is Low)
    if score < 60:
        st.markdown(f"""
        <div style="background:#fff7ed; border:1px solid #f97316; padding:15px; border-radius:10px; text-align:center; margin-top:20px;">
            <h4 style="color:#c2410c; margin:0;">{t['match_title']}</h4>
            <p style="font-size:13px; color:#9a3412;">Don't overpay. Compare with top-rated local pros.</p>
            <button style="background:#ea580c; color:white; border:none; padding:8px 16px; border-radius:5px; font-weight:bold;">{t['match_btn']}</button>
        </div>
        """, unsafe_allow_html=True)

    # ACTIONS
    st.markdown("---")
    c_act1, c_act2 = st.columns(2)
    pdf_data = create_pdf(t, project, region, name, status, addr, price, fair, diff, risk, detected_items)
    c_act1.download_button(label="📄 " + ("Download PDF" if lang == "English" else "Télécharger PDF"), data=pdf_data, file_name="QuoteGuard_Audit.pdf", mime="application/pdf")
    
    subject = urllib.parse.quote("Audit QuoteGuard")
    body = urllib.parse.quote(f"Price: {price}EUR\nFair: {fair}EUR")
    c_act2.markdown(f'<a href="mailto:?subject={subject}&body={body}" target="_blank" style="display:inline-block; padding:10px 20px; background-color:#334155; color:white; border-radius:5px; text-decoration:none;">{t["email_btn"]}</a>', unsafe_allow_html=True)
    
    if st.session_state.demo_mode:
        if st.button("🔄 Reset"): st.session_state.demo_mode = False; st.rerun()

else:
    # LANDING PAGE
    st.markdown("<br>", unsafe_allow_html=True)
    c_demo = st.container()
    col_d1, col_d2, col_d3 = c_demo.columns([1, 2, 1])
    with col_d2:
        if st.button(t["demo_btn"], type="primary", use_container_width=True): activate_demo(); st.rerun()
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("1. Select Region")
    with c2: st.info("2. Upload Quote/Image")
    with c3: st.info("3. Get Smart Audit")
    
    # PRICING
    st.markdown("---")
    st.markdown(f"### 💎 {t['upgrade_title']}")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown(f"""<div style="border:1px solid #E2E8F0; padding:20px; border-radius:10px;"><h4 style="margin:0;">{t['price_free']}</h4><h2>€0</h2><p style="font-size:12px">Automated AI Check</p>✅ {t['feat_1']}<br>✅ {t['feat_2']}</div>""", unsafe_allow_html=True)
    with cp2:
        st.markdown(f"""<div style="border:2px solid #22C55E; background:#F0FDF4; padding:20px; border-radius:10px;"><h4 style="margin:0; color:#166534;">{t['price_paid']}</h4><h2 style="color:#15803D;">€29</h2><p style="font-size:12px">Manual Review</p>✅ <b>{t['feat_4']}</b><br>✅ {t['feat_5']}<br><a href="{t['stripe_url']}" target="_blank" style="display:block; background:#166534; color:white; text-align:center; padding:10px; border-radius:6px; margin-top:10px; text-decoration:none;">{t['cta_paid']}</a></div>""", unsafe_allow_html=True)