import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 1. MAXIMIZE SCREEN SPACE ---
# This must be the very first Streamlit command!
st.set_page_config(layout="wide", page_title="Drive Search")

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Session State for results
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

def get_drive_service():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets not found! Check Streamlit settings.")
            st.stop()
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            key_dict, scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Auth Error: {str(e)}")
        st.stop()

def search_recursive(service, root_folder_id, query_text):
    """Crawls through folders starting at root_folder_id."""
    found_files = []
    folder_stack = [root_folder_id]
    
    # We use a placeholder in the sidebar for status updates so it doesn't clutter the main view
    status_text = st.sidebar.empty()
    
    while folder_stack:
        current_id = folder_stack.pop()
        try:
            q = (
                f"'{current_id}' in parents "
                f"and (name contains '{query_text}' or mimeType = 'application/vnd.google-apps.folder') "
                f"and trashed = false"
            )
            results = service.files().list(
                q=q, 
                fields="files(id, name, mimeType, webContentLink, thumbnailLink)",
                pageSize=1000 
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_stack.append(item['id'])
                if query_text.lower() in item['name'].lower() and "image/" in item.get('mimeType', ''):
                    found_files.append(item)
            
            status_text.text(f"Scanning... Found {len(found_files)} images...")
            
        except Exception as e:
            st.sidebar.warning(f"Skipped folder: {e}")
            
    status_text.empty()
    return found_files

# --- SIDEBAR UI (Controls) ---
with st.sidebar:
    st.title("📂 Drive Search")
    
    st.markdown("### Settings")
    default_id = "1V5nUlIgF783gDQA942Pl2XLxOKDDa0jK" 
    folder_id = st.text_input("Root Folder ID", value=default_id)
    if not folder_id:
        st.info("Paste ID from Drive URL above.")

    st.divider() # Adds a nice visual line

    # Search Form inside Sidebar
    with st.form("search_form", clear_on_submit=True):
        query_text = st.text_input("Filename", placeholder="e.g. invoice")
        submitted = st.form_submit_button("Search Drive", type="primary")

# --- MAIN UI (Results Only) ---
# Logic to run search
if submitted and query_text:
    if not folder_id:
        st.sidebar.warning("⚠️ Enter a Root Folder ID first.")
    else:
        service = get_drive_service()
        with st.spinner("Searching..."):
            results = search_recursive(service, folder_id, query_text)
            st.session_state.search_results = results
            st.session_state.last_query = query_text

# Display Results in Main Area
if st.session_state.last_query:
    st.subheader(f"Results for: {st.session_state.last_query}")

items = st.session_state.search_results

if items:
    # Now we can use 4 or 5 columns because we have the full screen width!
    cols = st.columns(5) 
    for index, item in enumerate(items):
        with cols[index % 5]:
            if 'thumbnailLink' in item:
                st.image(item['thumbnailLink'], use_column_width=True)
            
            # Clean name display
            st.caption(item['name'])
            st.markdown(f"[View Full]({item['webContentLink']})")

elif submitted:
    st.info("No images found.")