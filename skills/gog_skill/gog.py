import os.path
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents.readonly'
]

class GogSkill:
    name = "gog"
    description = "Integrated Google Services Agent."

    def __init__(self):
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # In a headless environment, this would need a manual code copy
                print("OAuth credentials missing. Please run 'python skills/gog_skill/gog.py --auth'")
                return

            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    def run(self, command, context):
        if not self.creds:
            return "Authentication required. Please set up GOG credentials."

        # Example: Gmail Search
        if "gmail search" in command:
            service = build('gmail', 'v1', credentials=self.creds)
            results = service.users().messages().list(userId='me', q='newer_than:1d').execute()
            return f"Found {len(results.get('messages', []))} recent emails."

        # Example: Sheets Get
        if "sheets get" in command:
            service = build('sheets', 'v4', credentials=self.creds)
            # Placeholder sheet logic
            return "Retrieved data from Google Sheets."

        return "GOG command not recognized or not yet implemented."

gog_skill = GogSkill()
