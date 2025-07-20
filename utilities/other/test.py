import requests
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import csv

import time

# Load env
load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

# Constants
URL = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
days = 195
start_time_utc = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
page = 1
all_orders = []

# Headers
headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}


retry_count = 0
max_retries = 5

while True:
    params = {
        "startDate": start_time_utc,
        "includeCancelled": "true",
        "orderType": "",
        "page": page
    }

    response = requests.get(URL, headers=headers, params=params)
    print(f"🔄 Page {page} - Status Code: {response.status_code}")

    if response.status_code == 601:
        retry_count += 1
        if retry_count > max_retries:
            print("❌ Too many retries. Exiting.")
            break
        wait_time = 45  # wait slightly longer than 40 sec
        print(f"⏳ Rate limit. Waiting {wait_time} sec...")
        time.sleep(wait_time)
        continue

    if response.status_code != 200:
        print("❌ Error:", response.text)
        break

    retry_count = 0  # reset on success

    data = response.json()
    orders = data.get("orders", [])
    if not orders:
        break

    all_orders.extend(orders)

    if page >= data.get("pageCount", 1):
        break

    page += 1
    print(f"✅ Page {page - 1} complete. Waiting 45 seconds before next...")
    time.sleep(45)  # 👈 necessary delay for CompletedOrders

print(f"✅ Total orders collected: {len(all_orders)}")

# Flatten orders to product-level rows
rows = []
for order in all_orders:
    for product in order.get("products", []):
        rows.append({
            "Order ID": order["id"],
            "Table": order.get("tableName"),
            "Waiter": order.get("waiterName"),
            "Order Total": order.get("orderTotal"),
            "Tax": order.get("taxAmount"),
            "Currency": order.get("currency"),
            "Insert Date": order.get("insertDate"),
            "Order Type": order.get("orderType"),
            "Status": order.get("status"),
            "Product": product["productName"],
            "Quantity": product["quantity"],
            "Unit Price": product["unitPrice"],
            "Total Product Price": product["totalAmount"],
            "Product Description": product.get("description") or "",
            "Features": ", ".join([f["featureName"] for f in product.get("features", [])])
        })

# Save to CSV
output_file = f"data/adisyo_completed_orders_full_{days}d.csv"
if rows:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"📁 Saved {len(rows)} rows to '{output_file}'")
else:
    print("⚠️ No data to write.")
