import streamlit as st
import pandas as pd
import time
import random

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
    """
    Loads the real data from your scraper.
    If the file is missing, it creates a 'Mock Database' so the app works anyway.
    """
    try:
        # Try to load the real CSV you scraped
        df = pd.read_csv("data/paris_fair_prices.csv")
        return df
    except FileNotFoundError:
        # FALLBACK: Mock data if you haven't run the scraper yet
        mock_data = {
            "Item_Name": ["Standard Toilet Pack", "Paint (White, 10L)", "Labor (Plumber / hour)", "Labor (Painter / hour)", "Water Heater 200L", "Travel Fee (Paris)"],
            "Price_Eur": [150.0, 60.0, 65.0, 45.0, 300.0, 50.0],
            "Category": ["Plumbing", "Painting", "Labor", "Labor", "Plumbing", "Fees"]
        }
        return pd.DataFrame(mock_data)

def analyze_quote(project_type):
    """
    Simulates the AI reading a PDF.
    Returns a 'Risk Score' and 'Detected Markup'.
    """
    time.sleep(2) # Fake processing delay to make it feel like AI
    
    # Randomly generate a "result" for the demo
    risk_level = random.choice(["Low", "Medium", "High"])
    
    if risk_level == "High":
        detected_markup = random.randint(150, 400) # 300% markup
        color = "inverse" # Red
        message = "⚠️ ALERT: Prices are significantly higher than market average."
    elif risk_level == "Medium":
        detected_markup = random.randint(20, 50)
        color = "normal" # Yellow/Black
        message = "⚖️ WARNING: Some items are expensive, but acceptable."
    else:
        detected_markup = random.randint(0, 10)
        color = "normal" # Green
        message = "✅ GOOD: This quote is fair and follows Paris standards."
        
    return risk_level, detected_markup, color, message

# --- FRONTEND (THE UI) ---

# 1. Header & Branding
col1, col2 = st.columns([1, 5])
with col1:
    st.write("## 🛡️") # You can replace this with st.image("logo.png") later
with col2:
    st.title("QuoteGuard AI (Paris Edition)")
    st.markdown("**The AI that protects Expats from Renovation Scams.** Upload your *Devis* to check if you are being overcharged.")

st.markdown("---")

# 2. Sidebar Controls
st.sidebar.header("⚙️ Project Settings")
language = st.sidebar.selectbox("Language", ["English", "Français"])
project_type = st.sidebar.selectbox("Project Type", ["Plumbing 🚿", "Electricity ⚡", "Painting 🎨", "General Renovation 🔨"])
st.sidebar.markdown("---")
st.sidebar.info("💡 **Did you know?** The average plumber in Paris charges €60-90/hour. Anything above €120 is usually a scam.")

# 3. File Upload Section
st.subheader("1. Upload your Quote (PDF or Image)")
uploaded_file = st.file_uploader("Drag & drop your 'Devis' here", type=["pdf", "jpg", "png"])

# 4. The "AI" Analysis Engine
if uploaded_file is not None:
    st.write("---")
    st.subheader("2. Analysis Report")
    
    with st.spinner('🕵️ AI is extracting line items and comparing with Leroy Merlin database...'):
        # Run the "Simulation"
        risk, markup, delta_color, msg = analyze_quote(project_type)
        
        # --- DASHBOARD METRICS ---
        kpi1, kpi2, kpi3 = st.columns(3)
        
        # Fake numbers for the demo (in a real app, these come from the OCR)
        quote_total = 1250
        fair_total = int(quote_total / (1 + markup/100))
        
        kpi1.metric("Quoted Price", f"€{quote_total}", f"{markup}% Overpriced", delta_color="inverse")
        kpi2.metric("Fair Market Value", f"€{fair_total}", "Based on 150+ datapoints")
        kpi3.metric("Scam Risk Score", risk, "Check Details Below", delta_color=delta_color)
        
        # Alert Box
        if risk == "High":
            st.error(msg)
        elif risk == "Medium":
            st.warning(msg)
        else:
            st.success(msg)

        # --- VISUALIZATION ---
        st.subheader("📊 Price Comparison by Item")
        
        # Create a Fake Comparison Dataframe for the Chart
        chart_data = pd.DataFrame({
            "Item": ["Labor (5h)", "Materials (Toilet)", "Travel Fee", "Consumables"],
            "Your Quote": [450, 600, 150, 50],
            "Fair Price": [300, 200, 50, 20]
        })
        
        # Transform for Bar Chart
        st.bar_chart(chart_data.set_index("Item"))
        
        # --- CTA (The Money Maker) ---
        st.markdown("---")
        st.subheader("💡 Don't sign this quote yet.")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Generate Negotiation Email (French)"):
                st.text_area("Copy this to your artisan:", 
                             f"Bonjour,\n\nJ'ai bien reçu votre devis de {quote_total}€.\nCependant, après vérification des prix du marché (Leroy Merlin & Tarifs Artisans Paris), ce montant semble élevé.\nLe prix moyen constaté pour ces travaux est de {fair_total}€.\n\nPouvons-nous revoir ce montant ?\n\nCordialement.")
        with c2:
            if st.button("🚨 Get a Verified Artisan Instead"):
                st.balloons()
                st.success("Request sent! Our verified partner will contact you within 2 hours.")

else:
    # Show some empty state stats to make it look professional
    st.info("👆 Please upload a file to start the analysis.")