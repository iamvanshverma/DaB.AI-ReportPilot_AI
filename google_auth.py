# google_auth.py
"""
Env-only Google OAuth helper for Streamlit (no /tmp client_secret.json usage).
Requires these environment variables to be set on the host (Render):
 - CLIENT_ID
 - CLIENT_SECRET
 - (optional) AUTH_URI         defaults to https://accounts.google.com/o/oauth2/auth
 - (optional) TOKEN_URI        defaults to https://oauth2.googleapis.com/token
 - (optional) REDIRECT_URIS    comma-separated list OR rely on APP_BASE_URL env
OR alternatively (single env):
 - GOOGLE_CLIENT_SECRET_JSON  (full client_secret JSON string) — still parsed into config
"""
import os
import json
import pathlib
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

CREDS_DIR = "/tmp/oauth_creds_env"  # persisted per-user creds on the host
os.makedirs(CREDS_DIR, exist_ok=True)


def _client_config_from_full_json_env():
    raw = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        # Accept both "web" and "installed" formats; normalize to "web"
        if "web" in parsed:
            return parsed
        if "installed" in parsed:
            return {"web": parsed["installed"]}
        # if the JSON already looks like the correct shape, return it
        return parsed
    except Exception:
        return None


def _client_config_from_parts():
    """
    Build client_config dict from individual env vars:
      CLIENT_ID, CLIENT_SECRET, AUTH_URI, TOKEN_URI, REDIRECT_URIS (comma-separated)
    REDIRECT_URIS falls back to APP_BASE_URL if provided.
    """
    client_id = os.getenv("CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None

    auth_uri = os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    token_uri = os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token")
    redirect_uris_raw = os.getenv("REDIRECT_URIS", "")
    redirect_uris = [u.strip() for u in redirect_uris_raw.split(",") if u.strip()]

    if not redirect_uris:
        app_base = os.getenv("APP_BASE_URL")
        if app_base:
            redirect_uris = [app_base.rstrip("/")]

    client_config = {
        "web": {
            "client_id": client_id,
            "project_id": os.getenv("PROJECT_ID", ""),
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": redirect_uris or ["http://localhost:8501"]
        }
    }
    return client_config


def _get_client_config():
    """
    Return a tuple (client_config_dict, client_secret_str)
    Raises RuntimeError if required env vars are missing.
    """
    cfg = _client_config_from_full_json_env()
    if cfg:
        # extract client_secret if present
        client_secret = cfg.get("web", {}).get("client_secret") or cfg.get("installed", {}).get("client_secret")
        return cfg, client_secret

    cfg = _client_config_from_parts()
    if cfg:
        client_secret = cfg["web"].get("client_secret")
        return cfg, client_secret

    # nothing found
    raise RuntimeError(
        "OAuth client config not found in environment. Set either GOOGLE_CLIENT_SECRET_JSON or "
        "CLIENT_ID + CLIENT_SECRET (and optionally REDIRECT_URIS or APP_BASE_URL)."
    )


def create_auth_url(app_base_url: str):
    """
    Create authorization URL and return (auth_url, state).
    app_base_url must exactly match one of the redirect_uris registered in GCP.
    """
    cfg, _ = _get_client_config()
    redirect_uri = app_base_url.rstrip("/")
    flow = Flow.from_client_config(cfg, scopes=SCOPES, redirect_uri=redirect_uri)
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return auth_url, state


def finish_oauth_and_get_service(query_params: dict, app_base_url: str):
    """
    Finalize OAuth exchange using code from query_params and return (email, sheets_service, creds_json).
    This function deliberately uses fetch_token(code=...) and passes client_secret explicitly when available.
    """
    cfg, client_secret = _get_client_config()
    state = query_params.get("state", [""])[0]
    redirect_uri = app_base_url.rstrip("/")

    flow = Flow.from_client_config(cfg, scopes=SCOPES, state=state, redirect_uri=redirect_uri)

    # Extract code reliably
    code = None
    if "code" in query_params:
        code = query_params.get("code", [""])[0]
    elif "authorization_response" in query_params:
        # parse code from full url if provided
        import urllib.parse as _up
        auth_resp = query_params.get("authorization_response", [""])[0]
        parsed = _up.urlparse(auth_resp)
        qd = _up.parse_qs(parsed.query)
        code = qd.get("code", [None])[0]

    if not code:
        if "error" in query_params:
            raise RuntimeError(f"OAuth provider returned error: {query_params.get('error')}")
        raise RuntimeError(
            "OAuth callback did not include an authorization code. Check that APP_BASE_URL exactly matches the Authorized redirect URI in Google Cloud Console."
        )

    # Exchange the code for tokens. Pass client_secret explicitly if available (safer for some setups).
    try:
        if client_secret:
            flow.fetch_token(code=code, client_secret=client_secret)
        else:
            flow.fetch_token(code=code)
    except Exception as e:
        # surface a helpful error without leaking secrets
        raise RuntimeError(
            f"OAuth token exchange failed. Ensure CLIENT_ID/CLIENT_SECRET or GOOGLE_CLIENT_SECRET_JSON are correct, "
            f"and APP_BASE_URL matches the authorized redirect URI. Underlying error: {e}"
        ) from e

    # Build credentials and services
    creds = flow.credentials
    oauth2 = build("oauth2", "v2", credentials=creds)
    userinfo = oauth2.userinfo().get().execute()
    email = userinfo.get("email", "unknown")

    # persist creds server-side (for demo/PoC). For production use encrypted DB.
    safe_email = email.replace("@", "_at_")
    dest = pathlib.Path(CREDS_DIR) / f"creds_{safe_email}.json"
    with open(dest, "w") as f:
        f.write(creds.to_json())

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
