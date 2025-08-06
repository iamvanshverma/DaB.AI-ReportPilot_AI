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
    token_path = 'token.pickle'
    
    # 1) Load existing token
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            creds = pickle.load(token_file)

    # 2) If no valid creds, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Read your OAuth client config from Streamlit secrets
            client_config = st.secrets["google_oauth"]
            
            # Write a temp file that includes the "installed" wrapper
            temp_path = "temp_oauth.json"
            payload = {"installed": dict(client_config)}
            with open(temp_path, "w") as f:
                json.dump(payload, f)
            
            # Run the desktop-app OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(temp_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Clean up
            os.remove(temp_path)

        # Cache the credentials for next time
        with open(token_path, 'wb') as token_file:
            pickle.dump(creds, token_file)

    # 3) Build and return the Sheets service
    return build('sheets', 'v4', credentials=creds)
