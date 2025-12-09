#!/usr/bin/env python3
"""
Home Depot API Client for Lead Collection
Fetches leads from HD ICONX API for MVendor 50020059 (Plumbing/Water Heater)
"""

import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class HDLeadsClient:
    """Client for fetching leads from Home Depot ICONX API"""

    def __init__(self, api_key: str, api_secret: str, mvendor_id: str = "50020059"):
        """
        Initialize the HD Leads Client

        Args:
            api_key: Your API key
            api_secret: Your API secret
            mvendor_id: MVendor ID (default: 50020059 for Plumbing)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.mvendor_id = mvendor_id
        self.base_url = "https://api.hs.homedepot.com/iconx/v1"

        # Create Base64 encoded credentials
        credentials = f"{api_key}:{api_secret}"
        self.credentials_base64 = base64.b64encode(credentials.encode()).decode()

        # Token management
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> Optional[str]:
        """Obtain OAuth access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        oauth_url = f"{self.base_url}/auth/accesstoken?grant_type=client_credentials"

        headers = {
            "Authorization": f"Basic {self.credentials_base64}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(oauth_url, headers=headers, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            expires_in = int(token_data.get("expires_in", 1800))
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"Error obtaining access token: {e}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        access_token = self._get_access_token()
        if not access_token:
            raise Exception("Failed to obtain access token")

        return {
            "appToken": access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def fetch_leads(
        self,
        days_back: int = 30,
        status_filter: Optional[str] = None,
        page_size: int = 100
    ) -> List[Dict]:
        """
        Fetch leads from the HD API

        Args:
            days_back: Number of days to look back
            status_filter: Optional status filter (e.g., 'New', 'Confirmed', 'Done')
            page_size: Number of results per page (max 100)

        Returns:
            List of lead dictionaries
        """
        url = f"{self.base_url}/leads/lookup"
        headers = self._get_headers()

        # Calculate date range
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y 00:00:00")

        # Build searchspec
        searchspec = f"([SFI MVendor #] = '{self.mvendor_id}' AND [Created] >= '{start_date}')"

        if status_filter:
            searchspec = f"([SFI MVendor #] = '{self.mvendor_id}' AND [Created] >= '{start_date}' AND [SFI Workflow Only Status ] = '{status_filter}')"

        all_leads = []
        start_row = 0

        while True:
            payload = {
                "SFILEADLOOKUPWS_Input": {
                    "PageSize": str(page_size),
                    "ListOfSfileadbows": {
                        "Sfileadheaderws": [{
                            "Searchspec": searchspec
                        }]
                    },
                    "StartRowNum": str(start_row)
                }
            }

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()

                leads_data = data.get("SFILEADLOOKUPWS_Output", {})
                leads_list = leads_data.get("ListOfSfileadbows", {}).get("Sfileadheaderws", [])

                if isinstance(leads_list, dict):
                    leads_list = [leads_list]

                if not leads_list:
                    break

                all_leads.extend(leads_list)

                # Check if this is the last page
                if leads_data.get("LastPage") == "true" or len(leads_list) < page_size:
                    break

                start_row += page_size

            except requests.exceptions.RequestException as e:
                print(f"Error fetching leads: {e}")
                break

        return all_leads

    def fetch_new_leads(self, days_back: int = 7) -> List[Dict]:
        """Fetch only new/unacknowledged leads"""
        return self.fetch_leads(days_back=days_back, status_filter="New")

    def fetch_confirmed_leads(self, days_back: int = 30) -> List[Dict]:
        """Fetch confirmed leads"""
        return self.fetch_leads(days_back=days_back, status_filter="Confirmed")

    def fetch_all_leads(self, days_back: int = 30) -> List[Dict]:
        """Fetch all leads regardless of status"""
        return self.fetch_leads(days_back=days_back)


if __name__ == "__main__":
    # Quick test
    API_KEY = "qkuDNmpbKpWghYAaceIurrv5fr2Jk3HB"
    API_SECRET = "HaPnI70Fj2Y2PEGQ"

    client = HDLeadsClient(API_KEY, API_SECRET, mvendor_id="50020059")

    print("Fetching leads from MVendor 50020059 (Plumbing)...")
    leads = client.fetch_leads(days_back=7)

    print(f"\nFound {len(leads)} leads:")
    for lead in leads[:5]:
        print(f"  {lead.get('Id')} - {lead.get('ContactFirstName')} {lead.get('ContactLastName')} - {lead.get('SFIWorkflowOnlyStatus')}")
