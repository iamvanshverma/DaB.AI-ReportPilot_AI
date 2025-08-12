# google_auth.py  (use this exact file)
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

CLIENT_SECRETS_PATH = "/tmp/client_secret.json"
CREDS_DIR = "/tmp/oauth_creds"
LOCAL_CLIENT_SECRET = "client_secret.json"

os.makedirs(CREDS_DIR, exist_ok=True)


def _client_config_from_env_parts():
    """
    Build client_config dict from individual env vars:
    CLIENT_ID, CLIENT_SECRET, AUTH_URI, TOKEN_URI, REDIRECT_URIS (optional comma-separated)
    """
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    auth_uri = os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    token_uri = os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token")
    redirect_uris_raw = os.getenv("REDIRECT_URIS", "")  # optional comma-separated
    redirect_uris = [u.strip() for u in redirect_uris_raw.split(",") if u.strip()]
    if not redirect_uris:
        # fallback to APP_BASE_URL if available
        app_base = os.getenv("APP_BASE_URL")
        if app_base:
            redirect_uris = [app_base.rstrip("/")]
    if not (client_id and client_secret):
        return None
    client_config = {
        "web": {
            "client_id": client_id,
            "project_id": os.getenv("PROJECT_ID", ""),
            "auth_uri": auth_uri,
            "token_uri": token_uri,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": redirect_uris or [os.getenv("APP_BASE_URL", "http://localhost:8501").rstrip("/")]
        }
    }
    return client_config


def _write_client_secrets_from_env_json(env_name="GOOGLE_CLIENT_SECRET_JSON", dest=CLIENT_SECRETS_PATH):
    raw = os.getenv(env_name)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        with open(dest, "w") as f:
            json.dump(parsed, f)
    except Exception:
        with open(dest, "w") as f:
            f.write(raw)
    return dest


def _ensure_client_secrets_file_or_config():
    """
    Returns a tuple (path_or_config, is_config_bool)
    If returns (path, False) it means use from_client_secrets_file(path)
    If returns (config, True) it means use from_client_config(config)
    """
    # 1) full JSON in env
    path = _write_client_secrets_from_env_json()
    if path and os.path.exists(path):
        return path, False

    # 2) individual env parts -> return config dict
    cfg = _client_config_from_env_parts()
    if cfg:
        return cfg, True

    # 3) local file fallback
    if os.path.exists(LOCAL_CLIENT_SECRET):
        return os.path.abspath(LOCAL_CLIENT_SECRET), False

    raise RuntimeError(
        "No OAuth client config found. Set GOOGLE_CLIENT_SECRET_JSON or (CLIENT_ID & CLIENT_SECRET) or place client_secret.json locally."
    )


def create_auth_url(app_base_url: str):
    obj, is_config = _ensure_client_secrets_file_or_config()
    redirect_uri = app_base_url.rstrip("/")
    if is_config:
        flow = Flow.from_client_config(obj, scopes=SCOPES, redirect_uri=redirect_uri)
    else:
        flow = Flow.from_client_secrets_file(obj, scopes=SCOPES, redirect_uri=redirect_uri)
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return auth_url, state


def finish_oauth_and_get_service(query_params: dict, app_base_url: str):
    obj, is_config = _ensure_client_secrets_file_or_config()
    state = query_params.get("state", [""])[0]
    redirect_uri = app_base_url.rstrip("/")
    if is_config:
        flow = Flow.from_client_config(obj, scopes=SCOPES, state=state, redirect_uri=redirect_uri)
    else:
        flow = Flow.from_client_secrets_file(obj, scopes=SCOPES, state=state, redirect_uri=redirect_uri)

    # build full auth response URL
    qp_items = []
    for k, v in query_params.items():
        for val in v:
            qp_items.append((k, val))
    auth_response = redirect_uri + "?" + urlencode(qp_items)

    flow.fetch_token(authorization_response=auth_response)
    creds = flow.credentials

    oauth2 = build("oauth2", "v2", credentials=creds)
    userinfo = oauth2.userinfo().get().execute()
    email = userinfo.get("email", "unknown")

    safe_email = email.replace("@", "_at_")
    dest = pathlib.Path(CREDS_DIR) / f"creds_{safe_email}.json"
    with open(dest, "w") as f:
        f.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)
    return email, service, creds.to_json()


def get_service_for_email(email: str):
    safe_email = email.replace("@", "_at_")
    path = pathlib.Path(CREDS_DIR) / f"creds_{safe_email}.json"
    if not path.exists():
        raise FileNotFoundError("Credentials for this user not found. Please sign in.")
    creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service
