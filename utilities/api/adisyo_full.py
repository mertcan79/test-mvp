import requests
import os
import csv
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

# Constants
URL = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
START_DATE = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
DATA_DIR = "data/full"
os.makedirs(DATA_DIR, exist_ok=True)
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

# Load or initialize progress
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r") as f:
        progress = json.load(f)
        page = progress.get("page", 1)
        total_written = progress.get("total_order_count", 0)
else:
    page = 1
    total_written = 0

# Open CSV files
orders_file = open(os.path.join(DATA_DIR, "orders.csv"), "a", newline="", encoding="utf-8")
products_file = open(os.path.join(DATA_DIR, "products.csv"), "a", newline="", encoding="utf-8")
features_file = open(os.path.join(DATA_DIR, "features.csv"), "a", newline="", encoding="utf-8")
payments_file = open(os.path.join(DATA_DIR, "payments.csv"), "a", newline="", encoding="utf-8")

orders_writer = products_writer = features_writer = payments_writer = None

# Prepare headers
headers = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

backoff_time = 60  # seconds, will grow on each 601 error
max_backoff = 1800  # 30 minutes max wait

while True:
    print(f"🔄 Page {page}")
    params = {
        "startDate": START_DATE,
        "includeCancelled": "true",
        "orderType": "",
        "page": page
    }

    response = requests.get(URL, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")


    if response.status_code == 601:
        print(f"⏳ Rate limit hit on page {page}. Waiting {backoff_time} seconds...")
        time.sleep(backoff_time)
        backoff_time = min(backoff_time * 2, max_backoff)
        continue  # Retry same page

    elif response.status_code != 200:
        print(f"❌ Unhandled error on page {page}: {response.text}")
        time.sleep(backoff_time)
        continue  # Retry same page after wait

    # Reset backoff after success
    backoff_time = 60

    data = response.json()
    orders = data.get("orders", [])
    if not orders:
        print("✅ No more orders.")
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
            if page == 1:
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
                if page == 1:
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
                    if page == 1:
                        features_writer.writeheader()
                features_writer.writerow(feature_row)

        # Write payments
        for payment in order.get("payments", []):
            payment_row = {
                "orderId": payment.get("orderId"),
                "paymentTypeId": payment.get("paymentTypeId"),
                "paymentName": payment.get("paymentName"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "exchangeRate": payment.get("exchangeRate"),
                "insertDate": payment.get("insertDate"),
                "customerId": payment.get("customerId"),
                "customerName": payment.get("customerName"),
                "customerSurname": payment.get("customerSurname"),
                "isDebit": payment.get("isDebit")
            }
            if not payments_writer:
                payments_writer = csv.DictWriter(payments_file, fieldnames=payment_row.keys())
                if page == 1:
                    payments_writer.writeheader()
            payments_writer.writerow(payment_row)

        total_written += 1

    # Save progress
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"page": page + 1, "total_order_count": total_written}, f)

    # Stop if finished
    if page >= data.get("pageCount", 1):
        print("✅ Finished all pages.")
        break

    print("✅ Waiting 45 sec before next page...")
    page += 1
    time.sleep(45)

# Close files
orders_file.close()
products_file.close()
features_file.close()
payments_file.close()
print(f"\n✅ All done. Total orders written: {total_written}")


