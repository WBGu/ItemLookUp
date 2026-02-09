import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

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

# --- RECURSIVE SEARCH FUNCTION ---
def search_recursive(service, root_folder_id, query_text):
    """
    Crawls through folders starting at root_folder_id.
    Returns a list of all matching files found in the tree.
    """
    found_files = []
    # The 'stack' is our to-do list of folders to search. Starts with the root.
    folder_stack = [root_folder_id]
    
    # Progress bar (optional, nice for deep searches)
    status_text = st.empty()
    
    # While there are folders left to check...
    while folder_stack:
        current_id = folder_stack.pop() # Get the next folder
        
        try:
            # SMART QUERY:
            # We ask for (Matches Name) OR (Is A Folder)
            # This lets us find the file, but ALSO find subfolders to add to our stack.
            q = (
                f"'{current_id}' in parents "
                f"and (name contains '{query_text}' or mimeType = 'application/vnd.google-apps.folder') "
                f"and trashed = false"
            )
            
            # Execute Search for this specific folder
            results = service.files().list(
                q=q, 
                fields="files(id, name, mimeType, webContentLink, thumbnailLink)",
                pageSize=1000 
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                # 1. If it's a folder, add it to the stack to be searched next
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_stack.append(item['id'])
                
                # 2. If it matches our name (and is an image), add to results
                # We check 'name in item' again because our API query included ALL folders regardless of name
                if query_text.lower() in item['name'].lower() and "image/" in item.get('mimeType', ''):
                    found_files.append(item)
            
            status_text.text(f"Scanning... Found {len(found_files)} images so far...")
            
        except Exception as e:
            st.warning(f"Skipped a folder due to error: {e}")
            
    status_text.empty() # Clear status when done
    return found_files

# --- MAIN UI ---
st.title("📂 Deep Drive Search")

with st.sidebar:
    st.header("Settings")
    default_id = "1V5nUlIgF783gDQA942Pl2XLxOKDDa0jK" 
    folder_id = st.text_input("Root Folder ID", value=default_id)
    st.info("Paste the ID from your Google Drive URL.")

with st.form("search_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        query_text = st.text_input("Search Filename", placeholder="e.g. invoice")
    with col2:
        submitted = st.form_submit_button("Search Tree")

# --- LOGIC ---
if submitted and query_text:
    if not folder_id:
        st.warning("⚠️ Enter a Root Folder ID first.")
    else:
        service = get_drive_service()
        
        with st.spinner("Crawling folders... this may take a moment..."):
            results = search_recursive(service, folder_id, query_text)
            
            st.session_state.search_results = results
            st.session_state.last_query = query_text

# --- DISPLAY ---
if st.session_state.last_query:
    st.write(f"Results for: **{st.session_state.last_query}**")

items = st.session_state.search_results

if items:
    cols = st.columns(2)
    for index, item in enumerate(items):
        with cols[index % 2]:
            if 'thumbnailLink' in item:
                st.image(item['thumbnailLink'], use_column_width=True)
            st.caption(item['name'])
            st.markdown(f"[View Full Size]({item['webContentLink']})")
elif submitted:
    st.info("No images found in this folder tree.")