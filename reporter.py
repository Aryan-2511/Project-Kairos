# reporter.py
import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def get_google_services():
    """Authenticates and returns Google Drive and Docs service objects."""
    # The entire JSON key is passed as a string in the GitHub secret
    service_account_info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    
    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return docs_service, drive_service

def create_and_save_google_doc(title: str, content: str):
    """Creates a Google Doc and saves it to the specified Drive folder."""
    DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID")
    print(f"---REPORTER: Creating Google Doc: {title}---")
    try:
        docs_service, drive_service = get_google_services()
        
        # Create the doc
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc['documentId']

        # Add the content
        requests_body = [{'insertText': {'location': {'index': 1}, 'text': content}}]
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests_body}).execute()
        
        # Move the doc to the specified folder
        drive_service.files().update(fileId=doc_id, addParents=DRIVE_FOLDER_ID, removeParents='root').execute()

        print(f"Successfully saved report to Google Drive.")
        return True
    except Exception as e:
        print(f"ERROR creating Google Doc: {e}")
        return False
