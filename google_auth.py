import streamlit as st
import json
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_gsheet_service():
    creds = None

    # 1) Try loading existing token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 2) If no valid creds, do OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # — Read your OAuth client JSON from Streamlit secrets —
            client_config = st.secrets["google_oauth"]
            temp_file = "temp_oauth.json"
            with open(temp_file, "w") as f:
                json.dump(dict(client_config), f)

            flow = InstalledAppFlow.from_client_secrets_file(temp_file, SCOPES)
            creds = flow.run_local_server(port=0)

            os.remove(temp_file)

        # 3) Cache the credentials for reuse
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # 4) Build and return the Sheets service
    return build('sheets', 'v4', credentials=creds)
