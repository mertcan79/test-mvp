import requests
import os
from dotenv import load_dotenv
import time
import csv

load_dotenv()

# Credentials and endpoint
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

URL = "https://ext.adisyo.com/api/External/v2/RecentOrders"

headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

# Send the request
response = requests.get(URL, headers=headers)
print("Status Code:", response.status_code)

if response.status_code == 200:
    data = response.json().get("data", [])

    # Prepare CSV rows
    orders_csv = []
    for order in data:
        row = {
            "Order ID": order.get("id"),
            "Customer Name": order.get("customer", {}).get("customerName"),
            "Order Total": order.get("orderTotal"),
            "Order Note": order.get("orderNote"),
            "Delivery App": order.get("externalAppName"),
            "Delivery Time": order.get("deliveryTime"),
            "Payment Method": order.get("paymentMethodName"),
            "Status": order.get("status"),
            "Insert Date": order.get("insertDate"),
            "City": order.get("customer", {}).get("city"),
            "Region": order.get("customer", {}).get("region"),
            "Product Count": len(order.get("products", [])),
            "Phone": order.get("customer", {}).get("customerPhone")
        }
        orders_csv.append(row)

    # Save to CSV
    filename = "data/adisyo_recent_orders.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=orders_csv[0].keys())
        writer.writeheader()
        writer.writerows(orders_csv)

    print(f"✅ Saved {len(orders_csv)} orders to '{filename}'.")

else:
    print("❌ Failed to fetch orders:", response.text)
