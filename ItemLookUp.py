import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Initialize Session State to hold results (so they stay when search bar clears)
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

def get_drive_service():
    """Authenticates using Streamlit Secrets and returns the Drive service."""
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets not found! Please check Streamlit settings.")
            st.stop()
            
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            key_dict, scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        st.stop()

# --- MAIN APP UI ---
st.title("📂 Drive Image Search")

# Sidebar for Folder ID
with st.sidebar:
    st.header("Settings")
    # Paste your ID here to save time, or leave empty to type it manually
    default_id = "" 
    folder_id = st.text_input("Google Drive Folder ID", value=default_id)
    st.info("Paste the ID from your Google Drive URL.")

# --- SEARCH FORM (The Magic Part) ---
# clear_on_submit=True ensures the text box empties after searching
with st.form("search_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # This input will clear automatically after you press Search
        query_text = st.text_input("Search Filename", placeholder="e.g. invoice, cat")
    
    with col2:
        # This button submits the form
        submitted = st.form_submit_button("Search")

# --- LOGIC ---
if submitted and query_text:
    if not folder_id:
        st.warning("⚠️ Please enter a Folder ID in the sidebar first.")
    else:
        service = get_drive_service()
        
        with st.spinner("Searching..."):
            try:
                # Construct Query
                q = (
                    f"name contains '{query_text}' "
                    f"and '{folder_id}' in parents "
                    f"and mimeType contains 'image/' "
                    f"and trashed = false"
                )
                
                # Execute Search
                results = service.files().list(
                    q=q, 
                    fields="files(id, name, webContentLink, thumbnailLink)"
                ).execute()
                
                # Save results to Session State so they persist
                st.session_state.search_results = results.get('files', [])
                st.session_state.last_query = query_text
                
            except Exception as e:
                st.error(f"Search failed: {str(e)}")

# --- DISPLAY RESULTS (Outside the form) ---
# We read from session_state, so the images stay visible even after the input clears
if st.session_state.last_query:
    st.write(f"Results for: **{st.session_state.last_query}**")

items = st.session_state.search_results

if items:
    # 2-column grid layout
    cols = st.columns(2)
    for index, item in enumerate(items):
        with cols[index % 2]:
            if 'thumbnailLink' in item:
                st.image(item['thumbnailLink'], use_column_width=True)
            else:
                st.write("No preview available")
            
            st.caption(item['name'])
            # Link to open in Drive
            st.markdown(f"[View Full Size]({item['webContentLink']})")
elif submitted and not items:
    st.info("No images found.")