
import os
import base64

from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():

    creds = None

    # Reuse saved authorization
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json", SCOPES
        )

    # Refresh or request authorization
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )

            creds = flow.run_local_server(port=0)

        # Save authorization for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(recipient, subject, body):

    try:

        service = get_gmail_service()

        message = EmailMessage()

        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        result = service.users().messages().send(
            userId="me",
            body={"raw": encoded_message}
        ).execute()

        return True, f"Email sent! Message ID: {result['id']}"

    except Exception as error:

        return False, str(error)