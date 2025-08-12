# google_auth.py
import os
import json
import pathlib
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Scopes: sheets + basic profile/email for identifying user
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

CLIENT_SECRETS_PATH = "/tmp/client_secret.json"
CREDS_DIR = "/tmp/oauth_creds"   # persisted per-user creds

os.makedirs(CREDS_DIR, exist_ok=True)

def _write_client_secrets_from_env(env_name="GOOGLE_CLIENT_SECRET_JSON", dest=CLIENT_SECRETS_PATH):
    """
    Writes client secrets JSON stored in env var to a file (used by Flow).
    """
    raw = os.getenv(env_name)
    if not raw:
        return None
    try:
        # if it's JSON string, pretty-write it
        parsed = json.loads(raw)
        with open(dest, "w") as f:
            json.dump(parsed, f)
    except Exception:
        with open(dest, "w") as f:
            f.write(raw)
    return dest

def create_auth_url(app_base_url: str):
    """
    Creates an authorization URL. Return (auth_url, state).
    app_base_url should be the exact redirect URI registered in GCP (e.g. "https://your-app.onrender.com")
    """
    _write_client_secrets_from_env()
    redirect_uri = app_base_url.rstrip("/")  # use root as redirect
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_PATH,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return auth_url, state

def finish_oauth_and_get_service(query_params: dict, app_base_url: str):
    """
    query_params: dict from streamlit's st.experimental_get_query_params()
    app_base_url: same redirect base used earlier
    Returns: (email, sheets_service, credentials_json_str)
    """
    _write_client_secrets_from_env()
    # Flatten query params (values may be lists)
    state = query_params.get("state", [""])[0]
    redirect_uri = app_base_url.rstrip("/")
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_PATH,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri
    )

    # Reconstruct the full authorization response URL expected by fetch_token
    qp_items = []
    for k, v in query_params.items():
        for val in v:
            qp_items.append((k, val))
    auth_response = redirect_uri + "?" + urlencode(qp_items)

    # Exchange code for tokens
    flow.fetch_token(authorization_response=auth_response)
    creds = flow.credentials

    # Get user email using oauth2 v2
    oauth2 = build("oauth2", "v2", credentials=creds)
    userinfo = oauth2.userinfo().get().execute()
    email = userinfo.get("email", "unknown")

    # persist creds for this user
    safe_email = email.replace("@", "_at_")
    dest = pathlib.Path(CREDS_DIR) / f"creds_{safe_email}.json"
    with open(dest, "w") as f:
        f.write(creds.to_json())

    # Build sheets service
    service = build("sheets", "v4", credentials=creds)
    return email, service, creds.to_json()

def get_service_for_email(email: str):
    """Load saved credentials for email and return sheets service (or raise)."""
    safe_email = email.replace("@", "_at_")
    path = pathlib.Path(CREDS_DIR) / f"creds_{safe_email}.json"
    if not path.exists():
        raise FileNotFoundError("Credentials for this user not found. Please sign in.")
    creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service
