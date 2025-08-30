import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError

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


def cleanup_old_files(drive_service, keep_last_n=5):
    """Deletes old files owned by the service account to free up quota."""
    print("⚠️ Cleaning up old files to free Drive quota...")
    try:
        results = drive_service.files().list(
            q="'me' in owners",
            pageSize=100,
            fields="files(id, name, createdTime)"
        ).execute()

        files = results.get("files", [])
        if not files:
            print("No files to clean up.")
            return

        # Sort by creation time (oldest first)
        files.sort(key=lambda f: f.get("createdTime", ""))

        # Keep the most recent N, delete the rest
        to_delete = files[:-keep_last_n] if len(files) > keep_last_n else []
        for f in to_delete:
            try:
                drive_service.files().delete(fileId=f["id"]).execute()
                print(f"🗑️ Deleted old file: {f['name']} ({f['id']})")
            except Exception as e:
                print(f"Failed to delete {f['name']}: {e}")

    except Exception as e:
        print(f"Cleanup failed: {e}")


def duplicate_to_personal_drive(drive_service, doc_id, title):
    """Makes a duplicate of the document in the user's personal Gmail Drive."""
    personal_email = os.environ.get("PERSONAL_EMAIL")
    if not personal_email:
        print("⚠️ PERSONAL_EMAIL not set, skipping duplication.")
        return

    try:
        copy = drive_service.files().copy(
            fileId=doc_id,
            body={"name": f"{title} (Copy for {personal_email})"}
        ).execute()

        # Share the copy with your Gmail
        drive_service.permissions().create(
            fileId=copy["id"],
            body={
                "type": "user",
                "role": "writer",
                "emailAddress": personal_email,
            },
        ).execute()

        print(f"📤 Duplicated doc into {personal_email}'s Drive: "
              f"https://docs.google.com/document/d/{copy['id']}/edit")

    except Exception as e:
        print(f"⚠️ Could not duplicate doc to personal Drive: {e}")


def create_and_save_google_doc(title: str, content: str):
    """Creates a Google Doc in the shared folder, writes content, and duplicates to personal Drive."""
    DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
    print(f"---REPORTER: Creating Google Doc: {title}---")

    docs_service, drive_service = get_google_services()

    try:
        # 1. Create the doc inside the shared folder using Drive API
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
        }
        if DRIVE_FOLDER_ID:
            file_metadata["parents"] = [DRIVE_FOLDER_ID]

        file = drive_service.files().create(body=file_metadata).execute()
        doc_id = file.get("id")

    except HttpError as e:
        if e.resp.status == 403 and "storageQuotaExceeded" in str(e):
            print("❌ Drive quota exceeded, attempting cleanup...")
            cleanup_old_files(drive_service)
            # Retry creation after cleanup
            file = drive_service.files().create(body=file_metadata).execute()
            doc_id = file.get("id")
        else:
            print(f"ERROR creating Google Doc: {e}")
            return False

    # 2. Insert content using Docs API
    requests_body = [{"insertText": {"location": {"index": 1}, "text": content}}]
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests_body}
    ).execute()

    # 3. Duplicate into your personal Drive
    duplicate_to_personal_drive(drive_service, doc_id, title)

    print(f"✅ Created doc (service account copy): https://docs.google.com/document/d/{doc_id}/edit")
    return True
