import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- 1. LAYOUT CONFIG ---
st.set_page_config(layout="wide", page_title="Drive Search")

# --- AUTH & SETUP ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""

def get_drive_service():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets not found!")
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
    """Crawls through folders."""
    found_files = []
    folder_stack = [root_folder_id]
    
    # Status indicator in sidebar to keep main area clean
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
                elif query_text.lower() in item['name'].lower() and "image/" in item.get('mimeType', ''):
                    found_files.append(item)
            
            status_text.text(f"Scanning... Found {len(found_files)} images...")
            
        except Exception as e:
            st.sidebar.warning(f"Error reading folder {current_id}: {e}")
            
    status_text.empty()
    return found_files

# --- 2. SIDEBAR (Title & Settings) ---
with st.sidebar:
    # Big Title is hidden away here to save main screen space
    st.title("📂 Drive Search")
    st.caption("v1.0 - Recursive Search")
    
    st.divider()
    
    st.markdown("**Settings**")
    default_id = "1V5nUlIgF783gDQA942Pl2XLxOKDDa0jK" 
    folder_id = st.text_input("Root Folder ID", value=default_id)
    if not folder_id:
        st.info("Paste ID from Drive URL.")

# --- 3. MAIN AREA (Search Bar & Results) ---

# We use columns to make the search bar centered and not too wide
# [1, 3, 1] means: "Space - Search Bar - Space"
col_left, col_mid, col_right = st.columns([1, 6, 1])

with col_mid:
    with st.form("search_form", clear_on_submit=True):
        # Search input and button side-by-side
        c1, c2 = st.columns([4, 1]) 
        with c1:
            query_text = st.text_input("Search", placeholder="Enter filename...", label_visibility="collapsed")
        with c2:
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

# Logic
if submitted and query_text:
    if not folder_id:
        st.error("⚠️ Please enter a Folder ID in the sidebar (left).")
    else:
        service = get_drive_service()
        with st.spinner("Searching entire folder tree..."):
            results = search_recursive(service, folder_id, query_text)
            st.session_state.search_results = results
            st.session_state.last_query = query_text

# Results Display
if st.session_state.last_query:
    st.markdown(f"### Results for: *{st.session_state.last_query}*")

items = st.session_state.search_results

if items:
    # Wide layout allows for 5 images per row
    cols = st.columns(5)
    for index, item in enumerate(items):
        with cols[index % 5]:
            if 'thumbnailLink' in item:
                st.image(item['thumbnailLink'], use_column_width=True)
            st.caption(item['name'])
            st.markdown(f"[View Full Size]({item['webContentLink']})")

elif submitted:
    st.info("No images found.")