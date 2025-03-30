# app/db/download_data.py
import os
import requests
import json

def download_card_data():
    db_path = "app/db/AllPrintings.json"
    
    # Skip if file already exists
    if os.path.exists(db_path):
        print(f"Card database already exists at {db_path}")
        return
        
    print("Downloading MTG card database (this may take a while)...")
    # Replace with actual download URL for your data source
    url = "https://mtgjson.com/api/v5/AllPrintings.json"
    
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, "wb") as f:
            f.write(response.content)
        print("Download complete!")
    else:
        print(f"Failed to download: {response.status_code}")

if __name__ == "__main__":
    download_card_data()