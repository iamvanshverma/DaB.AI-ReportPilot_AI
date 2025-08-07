import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Only Sheets-readonly scope is needed
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_gsheet_service():
    """
    Creates and returns a Google Sheets v4 service object
    using a service-account JSON stored in Streamlit secrets.
    """
    # 1) Read the entire service-account JSON dict from secrets
    sa_info = st.secrets["gcp_service_account"]

    # 2) Build Credentials object
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)

    # 3) Build & return the Sheets service
    service = build('sheets', 'v4', credentials=creds)
    return service

