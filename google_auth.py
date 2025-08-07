import streamlit as st
import json, os, pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_PATH = 'token.pickle'
TEMP_OAUTH = 'temp_oauth.json'

def get_gsheet_service():
    creds = None
    # 1) Pehle token cache dekh
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)

    # 2) Agar valid nahi hai, toh naya OAuth flow chala
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Secrets se client config lo
            cfg = st.secrets["google_oauth"]
            with open(TEMP_OAUTH, 'w') as f:
                json.dump({"installed": dict(cfg)}, f)

            flow = InstalledAppFlow.from_client_secrets_file(TEMP_OAUTH, SCOPES)
            # Browser open nahi, redirect URI pe hi handle karega
            creds = flow.run_local_server(
                host="0.0.0.0",
                port=8501,
                authorization_prompt_message="Apna browser mein jaake allow karo: {url}",
                open_browser=False
            )

            os.remove(TEMP_OAUTH)

        # 3) Naya token cache karo
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)

    # 4) Sheets service build karke return karo
    return build('sheets', 'v4', credentials=creds)

