"""
Live NAV Fetcher for Mutual Fund Schemes

This module fetches the latest historical NAV data from the MFAPI.in public API
for selected mutual fund schemes and saves them as individual CSV files in the
raw data directory.

It supports easy extension by adding new scheme names and their AMFI codes to
the mf_schemes dictionary.
"""

import requests
import pandas as pd

url = 'https://api.mfapi.in/mf/'
mf_schemes={
    "SBI_Bluechip": 125497,
    "Aditya_Birla_Sun_Life_Mutual_Fund": 119551, 
    "Axis_Mutual_Fund": 120503, 
    "Nippon_Large_Cap": 118632, 
    "HDFC_Mutual_Fund": 119092,
    "quant_Mutual_Fund": 120841
}

def fetch_live_nav():
    """
    Fetch latest NAV history for all schemes in mf_schemes and save as CSV files.
        """
    for name, amfiCode in mf_schemes.items():
        url = f"https://api.mfapi.in/mf/{amfiCode}"
        try: 
            res = requests.get(url)
            
            if res.status_code == 200:
                data = res.json()

                df = pd.DataFrame(data['data'])
                
                df['amfi_code'] = amfiCode            #inserting amfi_code column
                df = df[['amfi_code','date','nav']]   #reordering columns
                

                print(df)
                df.to_csv(f"../data/raw/amfi_live_nav_history_data/{name}_live_nav_history.csv" , index= False)

            else:
                print(f"Failed: {amfiCode}")

        except Exception as e:
            print(f"Error fetching {name}: {e}")

if __name__ == "__main__":
    fetch_live_nav()