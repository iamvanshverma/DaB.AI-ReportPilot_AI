# google_auth.py
"""
Google OAuth helper for Streamlit / Render deployments.

Provides:
    get_credentials_and_auth_url(query_params) -> (creds_or_None, auth_url_or_None)

Usage:
    qp = st.experimental_get_query_params()
    creds, auth_url = get_credentials_and_auth_url(qp)
    if auth_url:
        # show link to user
    else:
        # creds available -> use googleapiclient.discovery.build(..., credentials=creds)
"""

import os
import pickle
import logging
import requests

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TOKEN_FILE = "token.pickle"


def _load_token():
    """Load pickled Credentials if present."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)
            logger.info("Loaded token from %s", TOKEN_FILE)
            return creds
        except Exception as e:
            logger.exception("Failed to load token.pickle, ignoring: %s", e)
            return None
    return None


def _save_token(creds):
    """Persist Credentials to TOKEN_FILE."""
    try:
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        logger.info("Saved token to %s", TOKEN_FILE)
    except Exception:
        logger.exception("Failed to save token.pickle")


def _client_config():
    """
    Build minimal client_config dict expected by google_auth_oauthlib.flow.Flow.from_client_config
    using environment variables (so we don't require client_secret.json file on the server).
    """
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
    Main helper.

    Args:
        query_params: dict from st.experimental_get_query_params()

    Returns:
        (creds, None) if valid credentials available,
        (None, auth_url) if user must click auth link,
        raises exceptions for visible errors (so Streamlit/Render logs show full details).
    """
    creds = _load_token()

    # If token exists and is valid -> return it
    if creds and getattr(creds, "valid", False):
        return creds, None

    # If credentials expired but refresh token present -> refresh
    if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds, None
        except Exception:
            logger.exception("Refreshing stored credentials failed, will attempt new auth flow")

    # Check if the redirect from Google contains code
    code = None
    if isinstance(query_params, dict):
        codes = query_params.get("code")
        if codes:
            code = codes[0]

    client_config = _client_config()
    redirect_uri = os.getenv("APP_BASE_URL")  # MUST match exactly the redirect URI in GCP
    if not redirect_uri:
        raise RuntimeError("APP_BASE_URL must be set in environment (e.g. https://your-app.onrender.com/)")

    # Create Flow object with redirect_uri
    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=redirect_uri)

    if code:
        # Manual token exchange so we can log the full token endpoint response (debugable on Render).
        token_uri = client_config["web"].get("token_uri", os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token"))
        client_id = client_config["web"]["client_id"]
        client_secret = client_config["web"]["client_secret"]

        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            logger.info("Exchanging code for token at %s", token_uri)
            resp = requests.post(token_uri, data=payload, timeout=15)
            logger.info("Token endpoint status: %s", resp.status_code)
            logger.info("Token endpoint response: %s", resp.text)

            if resp.status_code != 200:
                # Raise so Streamlit shows the error and Render logs contain the raw response
                raise RuntimeError(f"Token exchange failed: {resp.status_code} - {resp.text}")

            token_data = resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise RuntimeError(f"Token response missing access_token: {token_data}")

            # Build Credentials object from token response
            creds = Credentials(
                token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_uri,
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )

            # Optionally set expiry if returned
            if "expires_in" in token_data:
                from datetime import datetime, timedelta
                creds.expiry = datetime.utcnow() + timedelta(seconds=int(token_data["expires_in"]))

            _save_token(creds)
            return creds, None

        except Exception:
            logger.exception("Manual token exchange failed")
            # Re-raise so Streamlit/Render surface the full failure
            raise

    # No code -> return auth URL user can click
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return None, auth_url
