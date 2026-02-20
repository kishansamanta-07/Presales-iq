import streamlit as st
import google.generativeai as genai
import requests

# 1. API Setup from Secrets
try:
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
    APOLLO_KEY = st.secrets.get("APOLLO_KEY", "")
    HUNTER_KEY = st.secrets.get("HUNTER_KEY", "")
    SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")
    genai.configure(api_key=GEMINI_KEY)
except Exception as e:
    st.error("Secrets configuration error.")

st.set_page_config(page_title="Sales IQ", layout="centered")
st.title("🚀 PreSales IQ")
st.markdown("### Powered by Kishan & Soumik's IQ")

# 2. Search Inputs
st.markdown("**Step 1: Company Intelligence**")
col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("Company Name*", placeholder="e.g. Larsen & Toubro")
with col2:
    city = st.text_input("City (Optional)", placeholder="e.g. Mumbai")

# --- THE UPDATED INDUSTRY DROPDOWN ---
industry = st.selectbox(
    "Select Industry Filter", 
    ("Auto-Detect", "Retail", "Manufacturing", "Distribution", "EPC", "Healthcare")
)

st.markdown("**Step 2: Direct Contact Hunter (Optional)**")
col3, col4 = st.columns(2)
with col3:
    target_name = st.text_input("Target Name", placeholder="e.g. S.N. Subrahmanyan")
with col4:
    domain = st.text_input("Company Domain", placeholder="e.g. larsentoubro.com")

# 3. Helper Functions
def get_live_google_data(query, api_key):
    if not api_key:
        return "SerpApi Key missing. Add to Streamlit Secrets to enable Google Search."
    try:
        import serpapi
        client = serpapi.Client(api_key=api_key)
        res = client.search({'engine': 'google', 'q': query, 'num': 3})
        
        snippets = []
        if 'organic_results' in res:
            for r in res['organic_results'][:3]:
                if 'snippet' in r:
                    snippets.append(r['snippet'])
        return "\n".join(snippets) if snippets else "No detailed data found on Google."
    except Exception as e:
        return f"Google Search failed: {e}"

def get_waterfall_contact(name, company_domain, apollo_key, hunter_key):
    contact_info = {"phone": "Not Found", "email": "Not Found", "source": "None"}
    if not apollo_key or not hunter_key:
        return {"phone": "API Keys Missing", "email": "API Keys Missing", "source": "Add keys to Streamlit Secrets"}

    parts = name.split()
    first_name = parts[0] if parts else ""
    last_name = parts[-1] if len(parts) > 1 else ""

    try:
        apollo_url = "https://api.apollo.io/v1/people/match"
        payload = {"api_key": apollo_key, "first_name": first_name, "last_name": last_name, "domain": company_domain}
        res = requests.post(apollo_url, json=payload).json()
        if 'person' in res and res['person']:
            contact_info['email'] = res['person'].get('email', "Not Found")
            contact_info['source'] = "Apollo.io"
    except:
        pass

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
        with st.spinner(f'Querying Google for {industry} metrics...'):
            contact_data_string = ""
            if target_name and domain:
                c_info = get_waterfall_contact(target_name, domain, APOLLO_KEY, HUNTER_KEY)
                contact_data_string = f"\nVERIFIED CONTACT FOUND:\n- Target: {target_name}\n- Email: {c_info['email']}\n- Phone: {c_info['phone']}\n- Data Source: {c_info['source']}\n"
            
            # --- DYNAMIC INDUSTRY ROUTING ---
            industry_metrics = {
                "Retail": "number of physical stores, e-commerce presence, and franchise vs owned model",
                "Manufacturing": "number of manufacturing plants, production capacity, and key product lines",
                "Distribution": "number of warehouses, distribution network span, and logistics scale",
                "EPC": "major ongoing/completed projects, order book value, and operational regions",
                "Healthcare": "hospital/clinic count, bed capacity, and key medical specialties",
                "Auto-Detect": "general scale, employee count, and primary revenue streams"
            }
            
            industry_search_terms = {
                "Retail": "number of stores",
                "Manufacturing": "manufacturing plants capacity",
                "Distribution": "warehouses logistics network",
                "EPC": "major projects order book",
                "Healthcare": "hospital beds clinics count",
                "Auto-Detect": "company scale size"
            }
            
            scale_focus = industry_metrics.get(industry, industry_metrics["Auto-Detect"])
            search_focus = industry_search_terms.get(industry, industry_search_terms["Auto-Detect"])
            
            search_query = f"{company_name} {city} headquarters address {search_focus} CEO LinkedIn"
            live_data = get_live_google_data(search_query, SERPAPI_KEY)

            try:
                safe_model = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name.lower() and 'preview' not in m.name.lower() and 'vision' not in m.name.lower():
                        safe_model = m.name
                        if 'flash' in m.name.lower(): break
                
                if safe_model:
                    model = genai.GenerativeModel(safe_model)
                    
                    prompt = f"""
                    Act as an elite B2B Sales Intelligence Expert. 
                    Analyze '{company_name}' ({city}, {industry} sector).
                    
                    LIVE GOOGLE DATA: {live_data}
                    {contact_data_string}
                    
                    Provide a highly structured Battle Card tailored for the {industry} industry:
                    
                    **1. 🏢 Company Profile & Footprint**
                    * **Registered Head Office:** (Extract exact address from Google data).
                    * **Operational Scale:** (Extract exact numbers focusing specifically on: {scale_focus}).
                    
                    **2. 👤 Key Decision Makers (KDMs) & LinkedIn**
                    * List the verified Names and Roles of top executives.
                    * **LinkedIn:** Provide a direct URL format to search for them (e.g., https://www.linkedin.com/search/results/people/?keywords={company_name}+CEO).
                    
                    **3. 📞 Direct Contact Intelligence**
                    * (If VERIFIED CONTACT FOUND is listed above, print it here. If not, suggest the corporate email pattern based on their domain).
                    
                    **4. 🎯 Strategic Sales Hooks**
                    * 3 custom, highly targeted talking points for a Presales meeting based specifically on their {industry} operations and current scale.
                    """
                    response = model.generate_content(prompt)
                    st.success(f"Deep Vertical Report Ready! (Tailored for {industry})")
                    st.markdown(response.text)
                    # --- THE NEW DOWNLOAD BUTTON ---
                    pdf_bytes = create_pdf(response.text, company_name)
                    st.download_button(
                        label="📄 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{company_name.replace(' ', '_')}_PreSales_IQ.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("No compatible model found.")
            except Exception as e:
                st.error(f"System Error: {e}")
