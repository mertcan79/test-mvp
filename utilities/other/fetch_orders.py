import requests
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import csv

# Load API keys
load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

# API endpoint
URL = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
days=180
# UTC start date for last 24 hours
start_time_utc = (datetime.now(timezone.utc) - timedelta(hours=24*days)).strftime("%Y-%m-%d %H:%M:%S")

# Query parameters
params = {
    "startDate": start_time_utc,
    "includeCancelled": "true",
    "orderType": "",
    "page": 10
}

# Required headers
headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

# Send GET request
response = requests.get(URL, headers=headers, params=params)
print("Status Code:", response.status_code)

if response.status_code == 200:
    orders = response.json().get("orders", [])

    # Prepare flattened rows
    rows = []
    for order in orders:
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

    # Write to CSV
    output_file = f"data/adisyo_completed_orders_{days}.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Saved {len(rows)} product rows from {len(orders)} orders to '{output_file}'")

else:
    print("❌ Error:", response.text)
