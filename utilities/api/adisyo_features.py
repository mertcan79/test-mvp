import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

URL = "https://ext.adisyo.com/api/External/v2/Features"

headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

response = requests.get(URL, headers=headers)
print("Status Code:", response.status_code)

if response.status_code == 200:
    feature_groups = response.json().get("data", {}).get("featureGroups", [])
    rows = []
    for group in feature_groups:
        for feature in group.get("features", []):
            related = feature.get("relatedProducts") or []
            for rel in related:
                rows.append({
                    "Group ID": group["featureGroupId"],
                    "Group Name": group["featuresGroupName"],
                    "Feature Name": feature["featureName"],
                    "Feature ID": feature["featureId"],
                    "Product ID": rel["productId"],
                    "Additional Price": rel["additionalPrice"],
                    "Header": rel["featureHeaderName"],
                    "Mandatory": group["necessaryCount"],
                    "Selection Type": group["featureHeaderType"]
                })

    with open("data/adisyo_features.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} feature rows to 'adisyo_features.csv'")
else:
    print("❌ Error:", response.text)
