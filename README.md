# Drive Deep Image Search

A Python Streamlit web application that allows you to securely and recursively search for images inside a specific Google Drive folder (and all of its subfolders). 

## Features
* **Recursive Search:** Crawls through a root folder and all nested subfolders to find your files.
* **Thumbnail Previews:** Displays a clean, 5-column grid of image thumbnails directly in the browser.
* **Direct Links:** One-click access to the full-size image in Google Drive.
* **Secure Authentication:** Uses Google Service Accounts ("Robot Accounts") so the app only sees the specific folders you explicitly share with it.
* **Responsive UI:** Maximized wide-screen layout with a collapsible sidebar for settings.

## Tech Stack
* **Frontend/Backend:** [Streamlit](https://streamlit.io/)
* **API:** Google Drive API v3
* **Authentication:** Google OAuth2 Service Accounts

---

## Setup & Installation

### Google Drive API Setup (Crucial)
Before running the app, you need a Google Service Account key.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and enable the **Google Drive API**.
3. Go to **IAM & Admin > Service Accounts** and create a new Service Account.
4. Go to the **Keys** tab for that account, click **Add Key > Create new key > JSON**. Download this file.
5. **Share your Drive Folder:** Open your normal Google Drive, right-click the folder you want the app to search, click **Share**, and share it with the exact *email address* of the Service Account you just created (e.g., `bot-name@project-id.iam.gserviceaccount.com`).

### Local Development (Running on your computer)
1. Clone this repository.
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
3. Create a folder named .streamlit in the root of the project, and inside it, create a file named secrets.toml.
4. Convert your downloaded JSON key into TOML format and paste it into secrets.toml:
	[gcp_service_account]
	type = "service_account"
	project_id = "..."
	private_key_id = "..."
	private_key = "..."
	client_email = "..."
	client_id = "..."
	auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
	token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
	auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
	client_x509_cert_url = "..."
5. Run the app:
	streamlit run ItemLookUp.py

### Deploying to Streamlit Cloud (Running on the web/mobile)

1. Push code (including ItemLookUp.py and requirements.txt) to a GitHub repository.
2. Go to Streamlit Community Cloud and create a new app linked to your repository.
3. Before launching, go to Advanced Settings > Secrets in the Streamlit dashboard.
4. Paste the exact same TOML formatted key block (from Step 2.4) into the Secrets text box.
5. Deploy the app!

