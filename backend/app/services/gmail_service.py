"""
Gmail API Service
Uses OAuth2 to send emails on behalf of the authenticated user.
Requires credentials.json downloaded from Google Cloud Console.
"""
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")


def _get_service():
    """Build and return an authenticated Gmail API service."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Gmail dependencies not installed. Run: "
            "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )

    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                raise RuntimeError(
                    "credentials.json not found. "
                    "Download it from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs → Download JSON. "
                    "Place it at backend/credentials.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    try:
        from googleapiclient.discovery import build
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        raise RuntimeError(f"Failed to build Gmail service: {e}")


def send_email(to: str, subject: str, body: str, sender: str = None) -> dict:
    """
    Send an email via Gmail API.
    Returns message_id on success.
    """
    service = _get_service()

    message = MIMEMultipart("alternative")
    message["to"] = to
    message["from"] = sender or os.getenv("GMAIL_SENDER", "me")
    message["subject"] = subject

    # Plain text part
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

    return {
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
        "status": "sent"
    }


def check_gmail_connected() -> dict:
    """Check if Gmail is authorized and credentials are valid."""
    if not os.path.exists(CREDS_FILE):
        return {
            "connected": False,
            "reason": "credentials.json not found",
            "setup_url": "https://console.cloud.google.com/apis/credentials"
        }
    if not os.path.exists(TOKEN_FILE):
        return {
            "connected": False,
            "reason": "Not yet authorized. Run the authorize endpoint first.",
            "authorized": False
        }
    try:
        _get_service()
        sender = os.getenv("GMAIL_SENDER", "")
        return {"connected": True, "sender": sender}
    except Exception as e:
        return {"connected": False, "reason": str(e)}


def authorize_gmail() -> dict:
    """
    Trigger the OAuth browser flow.
    Call this once from the terminal to generate token.json.
    """
    try:
        _get_service()
        return {"status": "authorized", "token_file": TOKEN_FILE}
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}
