# 🛡️ QuoteGuard AI

**An AI-powered digital consulting tool designed to verify renovation quotes, prevent financial scams, and empower homeowners in the Paris real estate market.**

🔗 **[Live Demo: Try QuoteGuard AI Here](https://quoteguard-ai-kbf5e98sqjbzi84jrvwqwq.streamlit.app/)**

---

## 📌 The Problem
The renovation market in Paris is highly opaque. Homeowners often lack the technical expertise to evaluate complex estimates (*devis*), leading to:
- **Massive Overpricing:** Contractors charging well above the fair market value.
- **Ghost Companies:** Unregistered or fraudulent contractors executing scams.
- **Information Asymmetry:** Clients struggling to negotiate without proper data.

## 💡 The Solution
**QuoteGuard AI** acts as a centralized intelligence and verification dashboard. Users simply upload their renovation quote (PDF), and the system automatically extracts critical data, cross-references it with real-time market benchmarks, and delivers an instant risk assessment.

## 🚀 Key Features

- 📄 **Automated PDF Parsing:** Instantly extracts the Quoted Price and Contractor's SIRET number from uploaded estimates.
- 📊 **Market Benchmarking:** Compares the extracted price against the "Fair Market Estimate" for France.
- 🚦 **Risk Verdict Engine:** Calculates the deviation percentage and categorizes the quote risk (e.g., Fair, Overpriced, High Risk).
- ⚖️ **Legal & Status Verification:** Evaluates the contractor's SIRET to ensure the business is legally registered.
- 💬 **AI Negotiation Script:** Generates a custom, data-backed script to help users negotiate better rates with their contractors.
- 📥 **Downloadable Audit:** Exports a complete, easy-to-read summary report of the analysis.

## 🛠️ Technology Stack

- **Frontend:** [Streamlit](https://streamlit.io/) (for a clean, responsive, and interactive UI)
- **Backend/Logic:** Python 3
- **Data Extraction:** PDF processing libraries (PyPDF2 / pdfplumber)
- **Data Handling:** Pandas, NumPy
- **Deployment:** Streamlit Community Cloud

## 💻 Local Installation & Setup

Create a virtual environment (Recommended):

Bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install the required dependencies:

Bash
pip install -r requirements.txt
Run the Streamlit application:

Bash
streamlit run app.py
🏗️ Future Roadmap
Integration with the official French Societe.com API for live SIRET fetching.

Natural Language Processing (NLP) to categorize specific renovation tasks (plumbing, electrical, etc.) from the PDF text.

Expansion to other major European housing markets.

👨‍💻 Author
Hussnain Amanat Ali Data Scientist | Digital Transformation Consultant

LinkedIn: https://www.linkedin.com/in/hussnainamanatali/

Location: Paris, France
