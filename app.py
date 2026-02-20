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

# 4. Search Execution
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Scouting the web for KDMs...'):
            model = genai.GenerativeModel('gemini-1.5-flash', tools=[{"google_search_retrieval": {}}])
            
            loc = f"in {city}" if city else "at their Headquarters"
            prompt = f"Analyze {company_name} {loc} in the {industry} sector. Find MD/CEO names, LinkedIn links, and 3 Ginesys-style sales hooks."
            
            response = model.generate_content(prompt)
            st.success("Report Ready!")
            st.markdown(response.text)
