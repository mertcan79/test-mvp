import requests
import os
from dotenv import load_dotenv
import csv

load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

URL = "https://ext.adisyo.com/api/External/v2/Products"

headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

response = requests.get(URL, headers=headers)
print("Status Code:", response.status_code)

if response.status_code == 200:
    categories = response.json().get("data", [])
    rows = []
    for cat in categories:
        for product in cat.get("products", []):
            for unit in product.get("productUnits", []):
                for price in unit.get("prices", []):
                    rows.append({
                        "Category": cat["categoryName"],
                        "Product Name": product["productName"],
                        "Product ID": product["productId"],
                        "Unit": unit["unitName"],
                        "Unit ID": unit["productUnitId"],
                        "Is Default Unit": unit["isDefault"],
                        "Tax Rate": product["taxRate"],
                        "Stock Follow": product["isStockFollow"],
                        "Price": price["price"],
                        "Order Type": price["orderType"]
                    })

    with open("data/adisyo_products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅ Saved {len(rows)} product entries to 'adisyo_products.csv'")
else:
    print("❌ Error:", response.text)
