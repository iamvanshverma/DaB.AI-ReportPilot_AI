import streamlit as st
import os, pickle, json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_PATH = 'token.pickle'
TEMP_OAUTH = 'temp_oauth.json'

def get_gsheet_service():
    creds = None

    # Token load karo agar hai
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)

    # Valid nahi hai toh naya OAuth flow chalao
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cfg = st.secrets["google_oauth"]

            with open(TEMP_OAUTH, 'w') as f:
                json.dump({"web": dict(cfg)}, f)

            flow = InstalledAppFlow.from_client_secrets_file(TEMP_OAUTH, SCOPES)
            creds = flow.run_local_server(
                host="0.0.0.0",
                port=8501,
                open_browser=True  # Streamlit Cloud ignores this
            )

            os.remove(TEMP_OAUTH)

        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)

    return build('sheets', 'v4', credentials=creds)
