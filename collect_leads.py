#!/usr/bin/env python3
"""
HD Leads Collector - Main Script
Fetches plumbing/water heater leads from Home Depot and saves to Google Sheets

Usage:
    python collect_leads.py                    # Fetch last 7 days, append new leads
    python collect_leads.py --days 30          # Fetch last 30 days
    python collect_leads.py --status New       # Only fetch new leads
    python collect_leads.py --replace          # Replace all data in sheet
"""

import argparse
import os
from datetime import datetime
from dotenv import load_dotenv

from hd_api_client import HDLeadsClient
from sheets_manager import SheetsManager

# Load environment variables
load_dotenv()

# Configuration
HD_API_KEY = os.getenv("HD_API_KEY", "qkuDNmpbKpWghYAaceIurrv5fr2Jk3HB")
HD_API_SECRET = os.getenv("HD_API_SECRET", "HaPnI70Fj2Y2PEGQ")
MVENDOR_ID = os.getenv("MVENDOR_ID", "50020059")  # Plumbing

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("SHEET_NAME", "Leads")


def main():
    parser = argparse.ArgumentParser(description="Collect HD Plumbing Leads")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--status", type=str, help="Filter by status (New, Confirmed, Done, etc.)")
    parser.add_argument("--replace", action="store_true", help="Replace all data instead of appending")
    parser.add_argument("--csv", type=str, help="Export to CSV file instead of Google Sheets")
    args = parser.parse_args()

    print("=" * 60)
    print("HD LEADS COLLECTOR - Plumbing/Water Heater")
    print("=" * 60)
    print(f"MVendor: {MVENDOR_ID}")
    print(f"Days back: {args.days}")
    print(f"Status filter: {args.status or 'All'}")
    print(f"Mode: {'Replace' if args.replace else 'Append'}")
    print()

    # Initialize HD API client
    print("Connecting to Home Depot API...")
    hd_client = HDLeadsClient(HD_API_KEY, HD_API_SECRET, mvendor_id=MVENDOR_ID)

    # Fetch leads
    print(f"Fetching leads from last {args.days} days...")
    leads = hd_client.fetch_leads(days_back=args.days, status_filter=args.status)
    print(f"Found {len(leads)} leads")

    if not leads:
        print("No leads found!")
        return

    # Show summary
    print("\nLead Summary:")
    status_counts = {}
    for lead in leads:
        status = lead.get('SFIWorkflowOnlyStatus', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    # Export to CSV if requested
    if args.csv:
        export_to_csv(leads, args.csv)
        return

    # Otherwise export to Google Sheets
    if not SPREADSHEET_ID:
        print("\nNo SPREADSHEET_ID configured. Set it in .env file.")
        print("Exporting to CSV instead...")
        export_to_csv(leads, f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        return

    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        print(f"\nGoogle credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
        print("Please set up Google Sheets API credentials.")
        print("Exporting to CSV instead...")
        export_to_csv(leads, f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        return

    # Connect to Google Sheets
    print(f"\nConnecting to Google Sheets...")
    sheets = SheetsManager(GOOGLE_CREDENTIALS_FILE, SPREADSHEET_ID)

    # Export leads
    if args.replace:
        print(f"Replacing all leads in '{SHEET_NAME}'...")
        count = sheets.replace_all_leads(leads, SHEET_NAME)
    else:
        print(f"Appending new leads to '{SHEET_NAME}'...")
        count = sheets.append_leads(leads, SHEET_NAME)

    print(f"\nDone! {count} leads exported to Google Sheets")


def export_to_csv(leads: list, filename: str):
    """Export leads to CSV file"""
    import csv

    headers = [
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
        'Description'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for lead in leads:
            row = [
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
                lead.get('Description', '')
            ]
            writer.writerow(row)

    print(f"\nExported {len(leads)} leads to {filename}")


if __name__ == "__main__":
    main()
