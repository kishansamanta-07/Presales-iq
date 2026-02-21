import streamlit as st
import google.generativeai as genai
import requests
from fpdf import FPDF
from supabase import create_client, Client

st.set_page_config(page_title="PreSales IQ", layout="wide")

# --- INITIALIZE MEMORY & AUTH ---
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'role' not in st.session_state:
    st.session_state['role'] = ""

# --- API SETUP ---
try:
    GEMINI_KEY = st.secrets.get("GEMINI_KEY", "")
    APOLLO_KEY = st.secrets.get("APOLLO_KEY", "")
    HUNTER_KEY = st.secrets.get("HUNTER_KEY", "")
    SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    genai.configure(api_key=GEMINI_KEY)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Secrets configuration error. Please check Streamlit Secrets.")

# ==========================================
# 🛑 LOGIN & SIGNUP SCREEN
# ==========================================
if not st.session_state['logged_in']:
    st.title("🔒 Welcome to PreSales IQ")
    st.markdown("### Enterprise Intelligence Platform")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.markdown("**Access your account**")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login"):
            try:
                res = supabase.table('app_users').select('*').eq('username', log_user).eq('password', log_pass).execute()
                if res.data:
                    user_data = res.data[0]
                    if user_data['status'] == 'approved':
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = user_data['username']
                        st.session_state['role'] = user_data['role']
                        st.rerun()
                    else:
                        st.warning("⏳ Your account is currently pending Admin approval.")
                else:
                    st.error("❌ Invalid Username or Password.")
            except Exception as e:
                st.error("Database connection error.")
                
    with tab2:
        st.markdown("**Request an account**")
        sign_user = st.text_input("Choose Username", key="sign_user")
        sign_pass = st.text_input("Choose Password", type="password", key="sign_pass")
        if st.button("Submit Request"):
            if sign_user and sign_pass:
                try:
                    # Check if username exists
                    check = supabase.table('app_users').select('*').eq('username', sign_user).execute()
                    if check.data:
                        st.error("Username already taken. Please choose another.")
                    else:
                        supabase.table('app_users').insert({'username': sign_user, 'password': sign_pass}).execute()
                        st.success("✅ Request submitted! You can log in once the Admin approves your account.")
                except Exception as e:
                    st.error("Error creating account.")
            else:
                st.warning("Please fill in both fields.")

# ==========================================
# 🟢 MAIN APPLICATION & ADMIN PANEL
# ==========================================
else:
    # --- SIDEBAR: ADMIN PANEL ---
    with st.sidebar:
        st.markdown(f"👋 **Logged in as:** {st.session_state['username'].upper()}")
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['history'] = []
            st.rerun()
            
        st.divider()
        
        if st.session_state['role'] == 'admin':
            st.title("👑 Admin Control Panel")
            st.markdown("**Pending Users:**")
            try:
                pending_users = supabase.table('app_users').select('*').eq('status', 'pending').execute()
                if not pending_users.data:
                    st.success("No pending requests.")
                else:
                    for p_user in pending_users.data:
                        st.warning(f"User: {p_user['username']}")
                        if st.button(f"Approve {p_user['username']}", key=f"app_{p_user['username']}"):
                            supabase.table('app_users').update({'status': 'approved'}).eq('username', p_user['username']).execute()
                            st.success(f"Approved {p_user['username']}!")
                            st.rerun()
            except Exception as e:
                st.error("Admin panel error.")
            st.divider()

        # --- SIDEBAR: HISTORY VAULT ---
        st.title("📚 History Vault")
        if not st.session_state['history']:
            st.info("No reports generated yet.")
        else:
            for i, record in enumerate(reversed(st.session_state['history'])):
                with st.expander(f"🏢 {record['company']} ({record['industry']})"):
                    st.markdown(record['report'])

    # --- THE ENGINE ROOM (Search UI) ---
    st.title("🚀 Einstien IQ Engine")
    
    st.markdown("**Step 1: Company Intelligence**")
    col1, col2 = st.columns([2, 1])
    with col1:
        company_name = st.text_input("Company Name*", placeholder="e.g. Larsen & Toubro")
    with col2:
        city = st.text_input("City (Optional)", placeholder="e.g. Mumbai")

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

    # Helper Functions
    def get_live_google_data(query, api_key):
        if not api_key: return "SerpApi Key missing."
        try:
            import serpapi
            client = serpapi.Client(api_key=api_key)
            res = client.search({'engine': 'google', 'q': query, 'num': 3})
            snippets = [r['snippet'] for r in res.get('organic_results', [])[:3] if 'snippet' in r]
            return "\n".join(snippets) if snippets else "No detailed data found."
        except Exception as e:
            return f"Search failed: {e}"

    def get_waterfall_contact(name, company_domain, apollo_key, hunter_key):
        contact_info = {"phone": "Not Found", "email": "Not Found", "source": "None"}
        if not apollo_key or not hunter_key: return contact_info
        parts = name.split()
        first_name = parts[0] if parts else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        try:
            res = requests.post("https://api.apollo.io/v1/people/match", json={"api_key": apollo_key, "first_name": first_name, "last_name": last_name, "domain": company_domain}).json()
            if 'person' in res and res['person']:
                contact_info['email'] = res['person'].get('email', "Not Found")
                phones = res['person'].get('phone_numbers', [])
                if phones: contact_info['phone'] = str(phones[0].get('sanitized_number', phones[0])) if isinstance(phones[0], dict) else str(phones[0])
                contact_info['source'] = "Apollo.io"
        except: pass

        if contact_info['email'] in ["Not Found", None, ""]:
            try:
                h_res = requests.get(f"https://api.hunter.io/v2/email-finder?domain={company_domain}&first_name={first_name}&last_name={last_name}&api_key={hunter_key}").json()
                if 'data' in h_res and 'email' in h_res['data']:
                    contact_info['email'] = h_res['data']['email']
                    contact_info['source'] = "Hunter.io"
            except: pass
        return contact_info

    def create_pdf(report_text, company):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"PreSales IQ Report: {company}", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=11)
        clean_text = report_text.replace('**', '').encode('latin-1', 'replace').decode('latin-1')
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 7, txt=line)
        return pdf.output(dest="S").encode('latin-1')

    # Search Execution
    if st.button("Generate Battle Card"):
        if not company_name:
            st.error("Please enter a company name.")
        else:
            with st.spinner(f'Querying Google for {industry} metrics...'):
                contact_data_string = ""
                if target_name and domain:
                    c_info = get_waterfall_contact(target_name, domain, APOLLO_KEY, HUNTER_KEY)
                    contact_data_string = f"\nVERIFIED CONTACT FOUND:\n- Target: {target_name}\n- Email: {c_info['email']}\n- Direct Phone: {c_info['phone']}\n- Data Source: {c_info['source']}\n"
                
                industry_metrics = {"Retail": "physical stores, e-commerce", "Manufacturing": "plants, capacity", "Distribution": "warehouses, logistics", "EPC": "projects, order book", "Healthcare": "hospital/clinic count, beds", "Auto-Detect": "scale, employees"}
                industry_search_terms = {"Retail": "number of stores", "Manufacturing": "plants capacity", "Distribution": "warehouses logistics", "EPC": "projects order book", "Healthcare": "hospital beds clinics", "Auto-Detect": "scale size"}
                
                scale_focus = industry_metrics.get(industry, industry_metrics["Auto-Detect"])
                search_focus = industry_search_terms.get(industry, industry_search_terms["Auto-Detect"])
                
                search_query = f"{company_name} {city} headquarters address corporate phone number {search_focus} CEO"
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
                        Analyze '{company_name}' ({city}, {industry}).
                        
                        LIVE GOOGLE DATA: {live_data}
                        {contact_data_string}
                        
                        Provide a highly structured Battle Card:
                        1. Company Profile & Footprint
                        * Registered Head Office: (From Google data).
                        * Operational Scale: (Focus on: {scale_focus}).
                        
                        2. Key Decision Makers (KDMs)
                        * List verified Names and Roles.
                        * LinkedIn: Provide URL format.
                        
                        3. Direct Contact Intelligence
                        * Target KDM: {target_name if target_name else "Not Specified"}
                        * Direct Email: (From VERIFIED CONTACT FOUND or suggest pattern).
                        * Direct Phone: (From VERIFIED CONTACT FOUND or 'Not available').
                        * HQ Phone: (From Google Data).
                        
                        4. Strategic Sales Hooks
                        * 3 custom Presales talking points based on their {industry} operations.
                        """
                        response = model.generate_content(prompt)
                        st.success("Report Ready!")
                        st.markdown(response.text)
                        
                        st.session_state['history'].append({"company": company_name, "industry": industry, "report": response.text})
                        
                        pdf_bytes = create_pdf(response.text, company_name)
                        st.download_button(label="📄 Download PDF Report", data=pdf_bytes, file_name=f"{company_name.replace(' ', '_')}_Report.pdf", mime="application/pdf")
                    else:
                        st.error("No compatible model found.")
                except Exception as e:
                    st.error(f"System Error: {e}")
