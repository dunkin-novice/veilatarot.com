import pandas as pd
import os
from datetime import datetime, timedelta

# Configuration
EXP_START_DATE = '2026-06-16'
SUBJECT_URLS = [
    'https://veilatarot.com/',
    'https://veilatarot.com/th/scenarios/kao-kid-kab-rao/',
    'https://veilatarot.com/th/scenarios/kao-ja-glab-ma/'
]

def analyze_gsc_data(csv_path):
    """
    Analyzes GSC 'Pages' export to track experiment performance.
    Expects a CSV from GSC with columns: Page, Impressions, Clicks, CTR, Position
    """
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}. Please export GSC data to this path.")
        return

    df = pd.read_csv(csv_path)
    
    print(f"--- SEO Experiment Analysis: Test 001 (Started: {EXP_START_DATE}) ---")
    
    for url in SUBJECT_URLS:
        page_data = df[df['Page'] == url]
        if not page_data.empty:
            pos = page_data['Position'].values[0]
            imp = page_data['Impressions'].values[0]
            print(f"URL: {url}")
            print(f"  Impressions: {imp}")
            print(f"  Avg Position: {pos}")
        else:
            print(f"URL: {url} - No data found in this export.")

if __name__ == "__main__":
    # Placeholder for manual path until automated GSC fetch is configured via Composio
    # analyze_gsc_data('gsc_export_2026-06-23.csv')
    print("SEO Tracker initialized. Ready for GSC data ingestion.")
