import requests
import os
import csv
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

# API setup
URL = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
start_time_utc = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

# Output files
orders_file = open("data/orders.csv", "w", newline="", encoding="utf-8")
products_file = open("data/products.csv", "w", newline="", encoding="utf-8")
features_file = open("data/features.csv", "w", newline="", encoding="utf-8")

orders_writer = None
products_writer = None
features_writer = None

page = 1
retry_count = 0
max_retries = 5
total_order_count = 0

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
        print("⏳ Rate limit hit. Sleeping 45 sec...")
        time.sleep(45)
        continue

    if response.status_code != 200:
        print("❌ Error:", response.text)
        break

    retry_count = 0
    data = response.json()
    orders = data.get("orders", [])
    if not orders:
        break

    for order in orders:
        # Write orders
        order_row = {
            "id": order.get("id"),
            "tableName": order.get("tableName"),
            "waiterName": order.get("waiterName"),
            "orderTotal": order.get("orderTotal"),
            "taxAmount": order.get("taxAmount"),
            "currency": order.get("currency"),
            "insertDate": order.get("insertDate"),
            "updateDate": order.get("updateDate"),
            "orderType": order.get("orderType"),
            "status": order.get("status"),
            "salesChannelName": order.get("salesChannelName"),
            "paymentMethodName": order.get("paymentMethodName"),
            "customerId": order.get("customerId"),
            "orderNumber": order.get("orderNumber")
        }
        if not orders_writer:
            orders_writer = csv.DictWriter(orders_file, fieldnames=order_row.keys())
            orders_writer.writeheader()
        orders_writer.writerow(order_row)

        # Write products
        for p in order.get("products", []):
            product_row = {
                "orderId": order.get("id"),
                "productName": p.get("productName"),
                "quantity": p.get("quantity"),
                "unitPrice": p.get("unitPrice"),
                "totalAmount": p.get("totalAmount"),
                "description": p.get("description"),
                "cancelReason": p.get("cancelReason"),
                "productId": p.get("productId"),
                "productCode": p.get("productCode"),
                "groupName": p.get("groupName"),
                "groupId": p.get("groupId")
            }
            if not products_writer:
                products_writer = csv.DictWriter(products_file, fieldnames=product_row.keys())
                products_writer.writeheader()
            products_writer.writerow(product_row)

            # Write features
            for f in p.get("features", []):
                feature_row = {
                    "orderId": order.get("id"),
                    "productId": p.get("productId"),
                    "featureName": f.get("featureName"),
                    "featureId": f.get("featureId"),
                    "additionalPrice": f.get("additionalPrice")
                }
                if not features_writer:
                    features_writer = csv.DictWriter(features_file, fieldnames=feature_row.keys())
                    features_writer.writeheader()
                features_writer.writerow(feature_row)

        total_order_count += 1

    if page >= data.get("pageCount", 1):
        break

    page += 1
    print("✅ Waiting 45 sec before next page...")
    time.sleep(45)

# Finalize
orders_file.close()
products_file.close()
features_file.close()
print(f"✅ Completed. Total orders written: {total_order_count}")
