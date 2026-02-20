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

# 4. Search Execution (WITH SMART FILTER)
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Selecting a safe, free-tier AI model...'):
            try:
                # SMART FILTER: Only grab standard Gemini models, ignore restricted ones
                safe_model = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        name = m.name.lower()
                        # Must be a Gemini model, but NOT a preview, vision, or research model
                        if 'gemini' in name and 'preview' not in name and 'research' not in name and 'vision' not in name:
                            safe_model = m.name
                            if 'flash' in name: # Prefer the flash model as it is the fastest
                                break 
                
                if not safe_model:
                    st.error("No free-tier text models available on this API key.")
                else:
                    # Use the safe model it just discovered
                    model = genai.GenerativeModel(safe_model)
                    
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
                    st.success(f"Report Ready! (Successfully used: {safe_model})")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"System Error: {e}")
