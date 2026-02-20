import streamlit as st
import google.generativeai as genai

# 1. Access the API Key from Secrets
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("API Key not found. Please configure it in Streamlit Secrets.")

# 2. Page Interface
st.set_page_config(page_title="PreSales IQ", layout="centered")
st.title("🚀 PreSales IQ")
st.markdown("### Universal B2B Intelligence Engine")

# 3. Search Inputs
col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("Company Name*", placeholder="e.g. Manyavar")
with col2:
    city = st.text_input("City (Optional)", placeholder="e.g. Kolkata")

industry = st.selectbox(
    "Select Industry Filter",
    ("Auto-Detect", "Retail", "Manufacturing", "EPC", "Distribution")
)

# 4. Search Execution (Updated Fix)
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Scouting the web for KDMs...'):
            # We use the standard model without the specific 'search' tool to avoid the 404 error
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            loc = f"in {city}" if city else "at their National Headquarters"
            
            # We give the AI clear instructions to use its internal knowledge + browsing
            prompt = f"""
            Act as a Lead Intelligence Specialist. 
            Research the company '{company_name}' {loc} within the {industry} sector.
            
            Find and provide:
            1. Likely names and LinkedIn roles for the MD, CEO, or IT Head.
            2. Company scale (number of employees or stores).
            3. A 'Ginesys-style' pitch: Why do they need retail/distribution automation?
            
            Format the output with bold headings and bullet points.
            """
            
            try:
                response = model.generate_content(prompt)
                st.success("Report Ready!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
