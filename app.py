import streamlit as st
import google.generativeai as genai

# 1. Access the API Key from Secrets
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("API Key not found in Streamlit Secrets.")

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

# 4. Search Execution (THE SMART AUTO-DETECT VERSION)
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Bypassing API locks and finding a working AI model...'):
            try:
                # DYNAMIC MODEL FINDER: This stops the 404 error forever.
                available_model = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_model = m.name
                        if '1.5-flash' in m.name: 
                            break # It found the best one, stop searching
                
                if not available_model:
                    st.error("Your API key is active, but Google hasn't unlocked any text models for it yet.")
                else:
                    # Use the model it just discovered
                    model = genai.GenerativeModel(available_model)
                    
                    loc = f"in {city}" if city else "at their National Headquarters"
                    
                    prompt = f"""
                    Act as a B2B Sales Intelligence Expert. 
                    Analyze the company '{company_name}' {loc} in the {industry} sector.
                    
                    Provide:
                    1. Likely Names/Roles of Decision Makers (MD, CEO, IT Head).
                    2. Business Scale & Presence.
                    3. 3 Strategic 'Hooks' for a Presales meeting.
                    
                    Format clearly with Bold Headings.
                    """
                    
                    response = model.generate_content(prompt)
                    st.success(f"Report Ready! (Successfully connected to: {available_model})")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"System Error: {e}")
