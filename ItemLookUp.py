import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticates using Streamlit Secrets and returns the Drive service."""
    try:
        # Check if secrets are loaded
        if "gcp_service_account" not in st.secrets:
            st.error("Secrets not found! Please add your 'gcp_service_account' block to Streamlit Secrets.")
            st.stop()
            
        # Load credentials from Secrets (dictionary format)
        key_dict = st.secrets["gcp_service_account"]
        
        # Create Credentials object
        creds = service_account.Credentials.from_service_account_info(
            key_dict, scopes=SCOPES
        )
        
        # Build and return the service
        return build('drive', 'v3', credentials=creds)
        
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        st.stop()

# --- MAIN APP UI ---
st.title("📂 Drive Image Search")

# 1. Sidebar for Setup (Optional, keeps main UI clean)
with st.sidebar:
    st.header("Settings")
    # You can hardcode your folder ID here if you want to skip typing it every time
    # default_folder = "YOUR_HARDCODED_FOLDER_ID"
    default_folder = "" 
    folder_id = st.text_input("Google Drive Folder ID", value=default_folder)
    folder_id = "1V5nUlIgF783gDQA942Pl2XLxOKDDa0jK"
    st.info("Paste the ID string from your Google Drive folder URL.")

# 2. Main Search Area
st.subheader("Search for an Image")
query_text = st.text_input("Enter filename (e.g., 'invoice', 'cat')")

# 3. Search Logic
if st.button("Search", type="primary"):
    
    if not folder_id:
        st.warning("⚠️ Please enter a Folder ID in the sidebar first.")
    elif not query_text:
        st.warning("⚠️ Please enter a filename to search for.")
    else:
        # Connect to Drive
        service = get_drive_service()
        
        with st.spinner("Searching Google Drive..."):
            try:
                # Construct Query: 
                # name contains 'text' AND inside 'folder' AND is an image AND not in trash
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
                
                items = results.get('files', [])

                # Display Results
                if not items:
                    st.info(f"No images found matching '{query_text}' in that folder.")
                else:
                    st.success(f"Found {len(items)} image(s)!")
                    
                    # Create a grid layout for images
                    cols = st.columns(2) # 2 images per row
                    for index, item in enumerate(items):
                        with cols[index % 2]:
                            st.image(item['thumbnailLink'], use_column_width=True)
                            st.caption(item['name'])
                            # Link to view full size
                            st.markdown(f"[View Full Size]({item['webContentLink']})")
                            
            except Exception as e:
                st.error(f"Search failed: {str(e)}")