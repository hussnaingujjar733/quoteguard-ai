import streamlit as st
import pandas as pd
import time
import random
import pdfplumber
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="QuoteGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BACKEND FUNCTIONS ---

@st.cache_data
def load_fair_prices():
    try:
        df = pd.read_csv("data/paris_fair_prices.csv")
        return df
    except FileNotFoundError:
        # Mock Database
        mock_data = {
            "Item_Name": ["Standard Toilet", "Paint 10L", "Labor (Hour)", "Water Heater"],
            "Price_Eur": [150.0, 60.0, 65.0, 300.0]
        }
        return pd.DataFrame(mock_data)

def extract_total_from_pdf(uploaded_file):
    """
    REAL AI: Opens the PDF and looks for the 'Total TTC' price.
    """
    text = ""
    total_price = 0.0
    
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
                
        # 1. Clean the text (remove currency symbols and spaces in numbers)
        # Look for patterns like "Total TTC : 1 250,00 €"
        # Regex explanation: Look for "Total" followed by "TTC" or "PAYER", then grab the number
        match = re.search(r"(?:Total|Montant)\s*(?:TTC|a payer|Net)?\s*[:\.]?\s*(\d[\d\s]*[.,]\d{2})", text, re.IGNORECASE)
        
        if match:
            price_str = match.group(1)
            # Fix French formatting (1 250,00 -> 1250.00)
            price_str = price_str.replace(" ", "").replace(",", ".")
            total_price = float(price_str)
            return total_price, True # True = Found real price
            
    except Exception as e:
        pass # If PDF is an image scan, extraction will fail, so we fallback
        
    return 0.0, False # False = Could not find price

def analyze_quote_logic(user_total, project_type):
    """
    Compares the User's Real Price vs Market Average
    """
    time.sleep(1.5) # Thinking...
    
    # Simple Logic: Define "Fair Caps" based on project type
    # (In the future, we sum up the line items individually)
    fair_ranges = {
        "Plumbing 🚿": 500,
        "Electricity ⚡": 800,
        "Painting 🎨": 1000,
        "General Renovation 🔨": 2000
    }
    
    fair_limit = fair_ranges.get(project_type, 1000)
    
    # Calculate Markup
    if user_total == 0:
        markup = 0 # No price found
    else:
        markup = int(((user_total - fair_limit) / fair_limit) * 100)
    
    # Determine Risk
    if markup > 50:
        return "High", markup, "inverse", f"⚠️ ALERT: This quote is {markup}% above the average market rate."
    elif markup > 10:
        return "Medium", markup, "normal", "⚖️ WARNING: Slightly expensive, but within range."
    else:
        return "Low", 0, "normal", "✅ GOOD: This price is fair."

# --- FRONTEND UI ---

col1, col2 = st.columns([1, 5])
with col1:
    st.write("## 🛡️")
with col2:
    st.title("QuoteGuard AI (V2.0)")
    st.markdown("**Real OCR Engine.** Upload a digital PDF to extract the exact price automatically.")
    st.caption("ℹ️ BETA: Works best with digital PDFs (not photo scans).")

st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Settings")
project_type = st.sidebar.selectbox("Project Type", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General Renovation 🔨"])

# File Upload
uploaded_file = st.file_uploader("📂 Upload Devis (PDF Only)", type=["pdf"])

if uploaded_file is not None:
    st.write("---")
    st.subheader("2. Analysis Report")
    
    with st.spinner('🤖 Reading document structure...'):
        
        # 1. RUN EXTRACTION
        extracted_price, success = extract_total_from_pdf(uploaded_file)
        
        # If extraction failed (e.g. it's an image scan), ask user manually
        if not success:
            st.warning("⚠️ Could not read the text (Is this a scanned image?). Please enter the total amount manually:")
            extracted_price = st.number_input("Total Price (€)", min_value=0.0, value=1000.0)
        
        # 2. RUN LOGIC
        risk, markup, delta_color, msg = analyze_quote_logic(extracted_price, project_type)
        
        # 3. DISPLAY RESULTS
        kpi1, kpi2, kpi3 = st.columns(3)
        
        fair_price = extracted_price / (1 + (markup/100)) if markup > 0 else extracted_price
        
        kpi1.metric("Quote Total", f"€{extracted_price:,.2f}", f"{markup}% Markup", delta_color="inverse")
        kpi2.metric("Fair Market Est.", f"€{fair_price:,.2f}")
        kpi3.metric("Risk Score", risk, delta_color=delta_color)
        
        if risk == "High":
            st.error(msg)
        elif risk == "Medium":
            st.warning(msg)
        else:
            st.success(msg)
            
        # 4. CTA
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.info("💡 Want to negotiate?")
            st.code(f"Bonjour, le prix moyen pour ce projet est de {fair_price:.0f}€. Pouvez-vous revoir votre devis ?", language="text")
        with c2:
            # YOUR WHATSAPP
            whatsapp_url = f"https://wa.me/33759823532?text=Help!%20I%20have%20a%20quote%20for%20{extracted_price}eur%20and%20need%20verification."
            st.link_button("🚨 Chat with an Expert (WhatsApp)", whatsapp_url)