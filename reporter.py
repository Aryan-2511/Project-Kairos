# reporter.py
import os
import json
import pickle
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials

def get_google_services():
    """Authenticate using OAuth (token.pickle) first, fallback to service account."""
    creds = None
    docs_service = None
    drive_service = None

    try:
        # ✅ OAuth flow (your personal Gmail)
        if os.path.exists("token.pickle"):
            print("🔑 Using OAuth token from token.pickle")
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            docs_service = build("docs", "v1", credentials=creds)
            drive_service = build("drive", "v3", credentials=creds)
            return docs_service, drive_service
    except Exception as e:
        print(f"⚠️ OAuth failed: {e}")

    try:
        # ✅ Fallback: Service Account
        print("🔑 Using Service Account authentication")
        service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents",
        ]
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        return docs_service, drive_service
    except Exception as e:
        print(f"❌ Both OAuth and Service Account failed: {e}")
        raise

def create_and_save_google_doc(title: str, content: str):
    """Creates a Google Doc and saves it to Drive."""
    DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
    print(f"---REPORTER: Creating Google Doc: {title}---")
    try:
        docs_service, drive_service = get_google_services()

        # Create doc
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]

        # Insert content
        requests_body = [
            {"insertText": {"location": {"index": 1}, "text": content}}
        ]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests_body}
        ).execute()

        # Move file to Drive folder if specified
        if DRIVE_FOLDER_ID:
            drive_service.files().update(
                fileId=doc_id, addParents=DRIVE_FOLDER_ID, removeParents="root"
            ).execute()

        print("✅ Successfully saved report to Google Drive.")
        return True
    except Exception as e:
        print(f"ERROR creating Google Doc: {e}")
        return False
