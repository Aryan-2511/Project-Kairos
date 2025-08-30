import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes needed
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents"
]

def get_google_services():
    """Authenticate using OAuth (your Gmail) and return Drive/Docs service objects."""
    creds = None
    # token.pickle stores your access/refresh tokens
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid creds, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save creds for future runs
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    drive_service = build("drive", "v3", credentials=creds)
    docs_service = build("docs", "v1", credentials=creds)
    return docs_service, drive_service


def create_and_save_google_doc(title: str, content: str):
    """Creates a Google Doc in YOUR Drive and writes content into it."""
    print(f"---REPORTER: Creating Google Doc: {title}---")
    docs_service, drive_service = get_google_services()

    # 1. Create new doc in your Drive
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document"
    }
    file = drive_service.files().create(body=file_metadata).execute()
    doc_id = file.get("id")

    # 2. Write content
    requests_body = [{"insertText": {"location": {"index": 1}, "text": content}}]
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests_body}
    ).execute()

    print(f"✅ Created doc in your Drive: https://docs.google.com/document/d/{doc_id}/edit")
    return True
