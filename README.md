# HD Leads Collector

Fetches Plumbing/Water Heater leads from Home Depot ICONX API and exports them to Google Sheets.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 3. Google Sheets Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create a Service Account and download credentials JSON
5. Save as `credentials.json` in this directory
6. Share your Google Sheet with the service account email

## Usage

### Fetch leads from last 7 days (default)
```bash
python collect_leads.py
```

### Fetch leads from last 30 days
```bash
python collect_leads.py --days 30
```

### Fetch only new leads
```bash
python collect_leads.py --status New
```

### Replace all data in sheet
```bash
python collect_leads.py --replace
```

### Export to CSV instead of Google Sheets
```bash
python collect_leads.py --csv leads.csv
```

## Lead Statuses

- `New` - New leads, not yet acknowledged
- `Acknowledged` - Lead acknowledged
- `Confirmed` - Appointment confirmed
- `Done` - Completed
- `Unqualified,SP Action Required` - Needs attention

## MVendor IDs

- `50005308` - MIAMI WATER AND AIR (Water Treatment)
- `50010710` - MIAMI WATER AND AIR-CR
- `50020059` - MIAMI WATER & AIR (Plumbing) - **Default**
