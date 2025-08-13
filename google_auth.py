# google_auth.py
import os
import pickle
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_FILE = "token.pickle"

def _load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            return pickle.load(f)
    return None

def _save_token(creds):
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)

def _client_config():
    # read client id/secret and token endpoints from env
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    auth_uri = os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    token_uri = os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token")

    if not client_id or not client_secret:
        raise RuntimeError("CLIENT_ID and CLIENT_SECRET must be set in environment")

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": auth_uri,
            "token_uri": token_uri
        }
    }

def get_credentials_and_auth_url(query_params):
    """
    Returns (credentials_obj or None, auth_url_or_None)
    - If credentials valid -> returns (creds, None)
    - If no creds and 'code' present in query_params -> exchanges code, returns (creds, None)
    - If no creds and no code -> returns (None, auth_url) so UI can show link
    query_params is dict from Streamlit: st.experimental_get_query_params()
    """
    creds = _load_token()

    # If token exists and valid -> return it
    if creds and getattr(creds, "valid", False):
        return creds, None

    # If token expired but refresh token present -> refresh
    if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds, None
        except Exception:
            # fallthrough to generate new auth url
            pass

    # If Google redirected back with code: exchange and save
    code = None
    if isinstance(query_params, dict):
        # st.experimental_get_query_params returns { 'code': ['...'] }
        codes = query_params.get("code")
        if codes:
            code = codes[0]

    client_config = _client_config()
    redirect_uri = os.getenv("APP_BASE_URL")  # MUST be the exact URL you registered in GCP
    if not redirect_uri:
        raise RuntimeError("APP_BASE_URL must be set in env (e.g. https://your-app.onrender.com/)")

    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)

    if code:
        # fetch token using the code
        flow.fetch_token(code=code)
        creds = flow.credentials
        _save_token(creds)
        return creds, None

    # No code -> return authorization URL for user to click
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return None, auth_url
