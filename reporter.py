import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def get_google_services():
    """Authenticates and returns Google Drive and Docs service objects."""
    service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
    ]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)

    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)
    return docs_service, drive_service


def create_and_save_google_doc(title: str, content: str):
    """Creates a Google Doc in the shared folder and writes content into it."""
    DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
    PERSONAL_EMAIL = os.environ.get("PERSONAL_EMAIL")  # put your Gmail in GitHub secret
    print(f"---REPORTER: Creating Google Doc: {title}---")
    try:
        docs_service, drive_service = get_google_services()

        # 1. Create the doc inside the shared folder using Drive API
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
        }
        if DRIVE_FOLDER_ID:
            file_metadata["parents"] = [DRIVE_FOLDER_ID]

        file = drive_service.files().create(body=file_metadata).execute()
        doc_id = file.get("id")

        # 2. Insert content using Docs API
        requests_body = [
            {"insertText": {"location": {"index": 1}, "text": content}}
        ]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests_body}
        ).execute()

        # 3. Transfer ownership (or at least share with you)
        if PERSONAL_EMAIL:
            try:
                drive_service.permissions().create(
                    fileId=doc_id,
                    body={
                        "type": "user",
                        "role": "owner",   # change to "writer" if transfer not allowed
                        "emailAddress": PERSONAL_EMAIL,
                    },
                    transferOwnership=True
                ).execute()
                print(f"✅ Ownership transferred to {PERSONAL_EMAIL}")
            except Exception as e:
                print(f"⚠️ Could not transfer ownership, sharing as editor instead: {e}")
                drive_service.permissions().create(
                    fileId=doc_id,
                    body={
                        "type": "user",
                        "role": "writer",
                        "emailAddress": PERSONAL_EMAIL,
                    }
                ).execute()

        print(f"✅ Created doc: https://docs.google.com/document/d/{doc_id}/edit")
        return True
    except Exception as e:
        print(f"ERROR creating Google Doc: {e}")
        return False
