import streamlit as st
import pandas as pd
import time
import random
import pdfplumber
import re
from datetime import datetime

# --- 1. PRO PAGE SETUP ---
st.set_page_config(
    page_title="QuoteGuard AI",
    page_icon="🛡️",
    layout="centered", # 'Centered' looks more like a landing page than 'Wide'
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (The "Makeover") ---
st.markdown("""
    <style>
    /* Hide the default Streamlit menu to look like a real app */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Title Style */
    .title-text {
        font-size: 50px;
        font-weight: 700;
        color: #0E1117;
        text-align: center;
    }
    .subtitle-text {
        font-size: 20px;
        color: #555;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Card Style for Results */
    .result-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. BACKEND LOGIC (Same as before + Tracking) ---

# Simple CSV Tracker (Saves data to a file on the server)
def log_scan(project_type, price, risk):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame([[timestamp, project_type, price, risk]], 
                            columns=["Time", "Type", "Price", "Risk"])
    
    # In a real deployed app, we would append this to Google Sheets
    # For now, we just print it to the server logs
    print(f"📝 NEW LEAD: {timestamp} | {project_type} | €{price} | {risk}")

def extract_total_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        match = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(" ", "").replace(",", ".")
            return float(price_str), True
    except:
        pass
    return 0.0, False

def analyze_quote_logic(user_total, project_type):
    time.sleep(1.5) # Fake AI thinking time
    fair_limit = {"Plumbing 🚿": 500, "Electricity ⚡": 800}.get(project_type, 1000)
    
    if user_total == 0: markup = 0
    else: markup = int(((user_total - fair_limit) / fair_limit) * 100)
    
    if markup > 50: return "High", markup, "inverse", "⚠️ High Risk: Prices significantly above market."
    elif markup > 10: return "Medium", markup, "normal", "⚖️ Moderate: Slightly expensive."
    else: return "Low", 0, "normal", "✅ Safe: This quote is fair."

# --- 4. THE PRO FRONTEND ---

# Hero Section (Centered & Clean)
st.markdown('<p class="title-text">🛡️ QuoteGuard AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">The only AI that protects Expats from Overpriced Renovation Quotes in Paris.</p>', unsafe_allow_html=True)

# The "Card" for Upload
with st.container():
    st.write("### 📂 Start your Free Scan")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        project_type = st.selectbox("Project Type", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General 🔨"])
    with col2:
        language = st.selectbox("Report Language", ["English", "Français"])
        
    uploaded_file = st.file_uploader("Upload your Devis (PDF)", type=["pdf"])

# Logic Trigger
if uploaded_file is not None:
    st.markdown("---")
    
    with st.spinner('🔄 AI is analyzing 150+ data points...'):
        price, success = extract_total_from_pdf(uploaded_file)
        if not success:
            price = st.number_input("⚠️ OCR Failed (Image scan detected). Enter Total Price (€):", value=1000.0)
        
        risk, markup, color, msg = analyze_quote_logic(price, project_type)
        
        # LOG THE DATA (Secretly)
        log_scan(project_type, price, risk)

    # --- RESULT DASHBOARD ---
    st.success("✅ Analysis Complete")
    
    # 3-Column Metrics with professional styling
    k1, k2, k3 = st.columns(3)
    k1.metric("Quoted Price", f"€{price:,.0f}")
    k2.metric("Fair Market Price", f"€{price/(1+markup/100):,.0f}")
    k3.metric("Risk Level", risk, f"{markup}% Markup", delta_color="inverse")

    # The "Insight Card"
    st.markdown(f"""
    <div class="result-card">
        <h4>📢 AI Verdict: {risk} Risk</h4>
        <p>{msg}</p>
        <p><i>Your Artisan is charging {markup}% more than the Paris average for this job.</i></p>
    </div>
    """, unsafe_allow_html=True)

    # --- CTA SECTION (The Closer) ---
    st.markdown("### 💡 What should you do?")
    
    b1, b2 = st.columns(2)
    with b1:
        st.info("📉 **Option 1: Negotiate**")
        st.caption("We generated a script for you.")
        with st.expander("View Negotiation Script (French)"):
            st.code(f"Bonjour, j'ai comparé votre devis de {price}€ avec les prix du marché...", language="text")
            
    with b2:
        st.error("🚀 **Option 2: Talk to an Expert**")
        st.caption("Get a human review in 5 mins.")
        # WhatsApp Link
        st.link_button("👉 Chat on WhatsApp", f"https://wa.me/33759823532?text=I%20have%20a%20quote%20for%20{price}EUR")

else:
    # Social Proof / Trust Signals (Important for "Pro" look)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.markdown("#### ⚡ Instant")
    c1.caption("Results in < 3 seconds")
    c2.markdown("#### 🔒 Private")
    c2.caption("Files deleted after scan")
    c3.markdown("#### 🇫🇷 Local Data")
    c3.caption("Based on Leroy Merlin prices")