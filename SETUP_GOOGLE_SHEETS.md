# Google Sheets Setup Guide

## Step 1: Create Service Account (One-time setup)

Since you already have project `sales-ai-agent-478815`, run these commands:

```bash
# Enable Sheets API
~/google-cloud-sdk/bin/gcloud services enable sheets.googleapis.com --project=sales-ai-agent-478815

# Create service account
~/google-cloud-sdk/bin/gcloud iam service-accounts create hd-leads-collector \
    --display-name="HD Leads Collector" \
    --project=sales-ai-agent-478815

# Download credentials
~/google-cloud-sdk/bin/gcloud iam service-accounts keys create credentials.json \
    --iam-account=hd-leads-collector@sales-ai-agent-478815.iam.gserviceaccount.com \
    --project=sales-ai-agent-478815
```

## Step 2: Create Google Sheet

1. Go to https://sheets.google.com
2. Create a new spreadsheet
3. Name it "HD Plumbing Leads" (or whatever you prefer)
4. Copy the Spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit`

## Step 3: Share Sheet with Service Account

1. In your Google Sheet, click "Share"
2. Add this email: `hd-leads-collector@sales-ai-agent-478815.iam.gserviceaccount.com`
3. Give it "Editor" access

## Step 4: Configure .env

```bash
cp .env.example .env
```

Edit `.env`:
```
HD_API_KEY=qkuDNmpbKpWghYAaceIurrv5fr2Jk3HB
HD_API_SECRET=HaPnI70Fj2Y2PEGQ
MVENDOR_ID=50020059
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=your_spreadsheet_id_here
SHEET_NAME=Leads
```

## Step 5: Test

```bash
python collect_leads.py --days 7
```

## Step 6: Set up Scheduled Runs (Optional)

Add to crontab for auto-sync every 30 minutes:
```bash
crontab -e
```

Add this line:
```
*/30 * * * * cd /home/matt/HD-Leads-Collector && python3 collect_leads.py --days 1 >> /tmp/hd-leads.log 2>&1
```
