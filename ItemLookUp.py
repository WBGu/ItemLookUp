import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Setup (Put your service_account.json in the same folder)
# In a real deployed app, you would put the JSON content in Streamlit "Secrets"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(
    'service_account.json', scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# 2. The GUI
st.title("Drive Image Search")

folder_id = st.text_input("Folder ID", "PASTE_YOUR_FOLDER_ID_HERE")
query_text = st.text_input("Search Filename")

if st.button("Search"):
    if query_text:
        # Search Query
        q = f"name contains '{query_text}' and '{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        results = service.files().list(q=q, fields="files(id, name, webContentLink)").execute()
        items = results.get('files', [])

        if not items:
            st.warning("No images found.")
        else:
            for item in items:
                st.write(f"Found: {item['name']}")
                # Streamlit can display Drive images directly via URL if permissions allow,
                # or you can download bytes like we did in Kivy. 
                # For simplicity, we just show the image:
                st.image(item['webContentLink'])