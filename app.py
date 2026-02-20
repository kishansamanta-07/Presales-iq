import streamlit as st
import google.generativeai as genai
import requests
from duckduckgo_search import DDGS

# 1. API Setup from Secrets
try:
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
    APOLLO_KEY = st.secrets.get("APOLLO_KEY", "")
    HUNTER_KEY = st.secrets.get("HUNTER_KEY", "")
    genai.configure(api_key=GEMINI_KEY)
except Exception as e:
    st.error("Gemini API Key not found in Streamlit Secrets.")

st.set_page_config(page_title="PreSales IQ", layout="centered")
st.title("🚀 PreSales IQ")
st.markdown("### Live Web & Contact Intelligence Engine")

# 2. Search Inputs
st.markdown("**Step 1: Company Intelligence**")
col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("Company Name*", placeholder="e.g. Manyavar")
with col2:
    city = st.text_input("City (Optional)", placeholder="e.g. Kolkata")

industry = st.selectbox("Select Industry Filter", ("Auto-Detect", "Retail", "Manufacturing", "EPC", "Distribution"))

st.markdown("**Step 2: Direct Contact Hunter (Optional)**")
col3, col4 = st.columns(2)
with col3:
    target_name = st.text_input("Target Name", placeholder="e.g. Ravi Modi")
with col4:
    domain = st.text_input("Company Domain", placeholder="e.g. manyavar.com")

# 3. Helper Functions
def get_live_web_data(query):
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([r['body'] for r in results])
    except:
        return "Live search failed."

def get_waterfall_contact(name, company_domain, apollo_key, hunter_key):
    contact_info = {"phone": "Not Found", "email": "Not Found", "source": "None"}
    if not apollo_key or not hunter_key:
        return {"phone": "API Keys Missing", "email": "API Keys Missing", "source": "Add keys to Streamlit Secrets"}

    parts = name.split()
    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""

    # Phase 1: Try Apollo
    try:
        apollo_url = "https://api.apollo.io/v1/people/match"
        payload = {"api_key": apollo_key, "first_name": first_name, "last_name": last_name, "domain": company_domain}
        res = requests.post(apollo_url, json=payload).json()
        if 'person' in res and res['person']:
            contact_info['email'] = res['person'].get('email', "Not Found")
            contact_info['source'] = "Apollo.io"
    except:
        pass

    # Phase 2: Try Hunter if Email is missing
    if contact_info['email'] in ["Not Found", None, ""]:
        try:
            hunter_url = f"https://api.hunter.io/v2/email-finder?domain={company_domain}&first_name={first_name}&last_name={last_name}&api_key={hunter_key}"
            h_res = requests.get(hunter_url).json()
            if 'data' in h_res and 'email' in h_res['data']:
                contact_info['email'] = h_res['data']['email']
                contact_info['source'] = "Hunter.io"
        except:
            pass
            
    return contact_info

# 4. Search Execution
if st.button("Generate Battle Card"):
    if not company_name:
        st.error("Please enter a company name.")
    else:
        with st.spinner('Hunting for data...'):
            contact_data_string = ""
            if target_name and domain:
                c_info = get_waterfall_contact(target_name, domain, APOLLO_KEY, HUNTER_KEY)
                contact_data_string = f"\nVERIFIED CONTACT FOUND:\n- Target: {target_name}\n- Email: {c_info['email']}\n- Phone: {c_info['phone']}\n- Data Source: {c_info['source']}\n"
            
            search_query = f"{company_name} {city} {industry} headquarters CEO"
            live_data = get_live_web_data(search_query)

            try:
                safe_model = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name.lower() and 'preview' not in m.name.lower() and 'vision' not in m.name.lower():
                        safe_model = m.name
                        if 'flash' in m.name.lower(): break
                
                if safe_model:
                    model = genai.GenerativeModel(safe_model)
                    prompt = f"""
                    Act as a B2B Sales Intelligence Expert. 
                    Analyze '{company_name}' ({city}, {industry}).
                    
                    LIVE WEB DATA: {live_data}
                    {contact_data_string}
                    
                    Provide a Battle Card:
                    1. Verified Decision Makers (from the web data).
                    2. Verified Scale/Presence.
                    3. Direct Contact Info (If VERIFIED CONTACT FOUND is listed above, print it exactly. If not, suggest the likely corporate email pattern).
                    4. 3 Strategic 'Hooks' for a Presales meeting.
                    """
                    response = model.generate_content(prompt)
                    st.success("Report Ready!")
                    st.markdown(response.text)
                else:
                    st.error("No compatible model found.")
            except Exception as e:
                st.error(f"System Error: {e}")
