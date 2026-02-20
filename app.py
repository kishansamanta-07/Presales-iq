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

# 4. Search Execution (STABLE VERSION)
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Analyzing industry data...'):
            # WE REMOVED THE "TOOLS" LINE - This is the fix!
            model = genai.GenerativeModel('gemini-1.5-flash')
            
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
            
            try:
                # Direct call without the search retrieval tool
                response = model.generate_content(prompt)
                st.success("Analysis Complete!")
                st.markdown(response.text)
                st.download_button("Download Report", response.text, file_name=f"{company_name}_Report.txt")
            except Exception as e:
                st.error(f"Error: {e}. Try changing model name to 'gemini-pro' in code.")
