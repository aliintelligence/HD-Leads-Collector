#!/usr/bin/env python3
"""
Google Sheets Manager for HD Leads
Handles exporting leads to Google Sheets
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsManager:
    """Manager for Google Sheets operations"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Column headers for the leads sheet
    HEADERS = [
        'Service Center ID',
        'Order Number',
        'Created Date',
        'Status',
        'First Name',
        'Last Name',
        'Phone',
        'Cell Phone',
        'Email',
        'Address',
        'City',
        'State',
        'Zip Code',
        'Store Number',
        'Store Name',
        'Program',
        'MVendor',
        'Description',
        'Question Answers',
        'Notes',
        'Last Updated'
    ]

    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Initialize the Sheets Manager

        Args:
            credentials_file: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self._connect()

    def _connect(self):
        """Connect to Google Sheets API"""
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=creds)
            print("Connected to Google Sheets API")
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            raise

    def _ensure_headers(self, sheet_name: str = "Leads"):
        """Ensure headers exist in the sheet"""
        try:
            # Check if headers exist
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1:U1"
            ).execute()

            values = result.get('values', [])

            if not values or values[0] != self.HEADERS:
                # Set headers
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A1:U1",
                    valueInputOption='RAW',
                    body={'values': [self.HEADERS]}
                ).execute()
                print(f"Headers set in {sheet_name}")

        except HttpError as e:
            if e.resp.status == 400:
                # Sheet might not exist, try to create it
                self._create_sheet(sheet_name)
                self._ensure_headers(sheet_name)
            else:
                raise

    def _create_sheet(self, sheet_name: str):
        """Create a new sheet tab"""
        try:
            request = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=request
            ).execute()
            print(f"Created sheet: {sheet_name}")
        except HttpError as e:
            print(f"Error creating sheet: {e}")

    def _extract_notes(self, lead: Dict) -> str:
        """Extract notes from lead and combine into a single string"""
        notes_data = lead.get('ListOfSfinotesws')
        if not notes_data:
            return ''

        notes_list = notes_data.get('Sfinotesws', [])
        if isinstance(notes_list, dict):
            notes_list = [notes_list]

        # Combine all notes with timestamps
        notes_text = []
        for note in notes_list:
            note_text = note.get('Note', '')
            if note_text:
                created = note.get('Created', '')
                notes_text.append(f"[{created}] {note_text}")

        return ' | '.join(notes_text)

    def _lead_to_row(self, lead: Dict) -> List:
        """Convert a lead dictionary to a row"""
        return [
            lead.get('Id', ''),
            lead.get('MMSVCSServiceProviderOrderNumber', ''),
            lead.get('Created', ''),
            lead.get('SFIWorkflowOnlyStatus', ''),
            lead.get('ContactFirstName', ''),
            lead.get('ContactLastName', ''),
            lead.get('MMSVPreferredContactPhoneNumber', '') or lead.get('SFIContactHomePhone', ''),
            lead.get('CellularPhone', ''),
            lead.get('MainEmailAddress', ''),
            lead.get('MMSVSiteAddress', ''),
            lead.get('MMSVSiteCity', ''),
            lead.get('MMSVSiteState', ''),
            lead.get('MMSVSitePostalCode', ''),
            lead.get('MMSVStoreNumber', ''),
            lead.get('MMSVStoreName', ''),
            lead.get('SFIProgramGroupNameUnconstrained', ''),
            lead.get('SFIMVendor', ''),
            lead.get('Description', ''),
            lead.get('MMSVQuestionAnswers', ''),
            self._extract_notes(lead),
            datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        ]

    def get_existing_lead_ids(self, sheet_name: str = "Leads") -> set:
        """Get set of existing Service Center IDs in the sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A"
            ).execute()

            values = result.get('values', [])
            # Skip header row, get all IDs
            return set(row[0] for row in values[1:] if row)

        except HttpError:
            return set()

    def append_leads(self, leads: List[Dict], sheet_name: str = "Leads", skip_duplicates: bool = True):
        """
        Append leads to the spreadsheet

        Args:
            leads: List of lead dictionaries
            sheet_name: Name of the sheet tab
            skip_duplicates: If True, skip leads that already exist
        """
        self._ensure_headers(sheet_name)

        if skip_duplicates:
            existing_ids = self.get_existing_lead_ids(sheet_name)
            leads = [l for l in leads if l.get('Id') not in existing_ids]

        if not leads:
            print("No new leads to add")
            return 0

        rows = [self._lead_to_row(lead) for lead in leads]

        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:U",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': rows}
            ).execute()

            updates = result.get('updates', {})
            rows_added = updates.get('updatedRows', len(rows))
            print(f"Added {rows_added} leads to {sheet_name}")
            return rows_added

        except HttpError as e:
            print(f"Error appending leads: {e}")
            return 0

    def replace_all_leads(self, leads: List[Dict], sheet_name: str = "Leads"):
        """
        Replace all leads in the sheet (clear and re-add)

        Args:
            leads: List of lead dictionaries
            sheet_name: Name of the sheet tab
        """
        try:
            # Clear existing data (keep headers)
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A2:U"
            ).execute()
            print(f"Cleared existing data in {sheet_name}")

        except HttpError:
            pass  # Sheet might be empty

        # Add all leads
        return self.append_leads(leads, sheet_name, skip_duplicates=False)


if __name__ == "__main__":
    # Test connection
    CREDENTIALS_FILE = "credentials.json"
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

    if os.path.exists(CREDENTIALS_FILE):
        manager = SheetsManager(CREDENTIALS_FILE, SPREADSHEET_ID)
        print("Sheets manager initialized successfully")
    else:
        print(f"Credentials file not found: {CREDENTIALS_FILE}")
        print("Please download your Google service account credentials")
