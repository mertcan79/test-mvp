import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

URL = "https://ext.adisyo.com/api/External/v2/Couriers"

headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

response = requests.get(URL, headers=headers)
print("Status Code:", response.status_code)

if response.status_code == 200:
    couriers = response.json().get("Couriers", [])
    with open("data/adisyo_couriers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Id", "Name", "PhoneNumber"])
        writer.writeheader()
        writer.writerows(couriers)
    print(f"✅ Saved {len(couriers)} couriers to 'adisyo_couriers.csv'")
else:
    print("❌ Error:", response.text)
