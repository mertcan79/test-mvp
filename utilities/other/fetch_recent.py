import requests
import os
import csv
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load credentials
load_dotenv()
API_KEY = os.getenv("adisyo_web_siparis")
API_SECRET = os.getenv("adisyo_api")
CONSUMER = os.getenv("adisyo_id")

# API endpoint
URL = "https://ext.adisyo.com/api/External/v2/RecentOrders"
HEADERS = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "Content-Type": "application/json"
}

# Output CSV files
os.makedirs("data", exist_ok=True)
orders_file = open("data/recent_orders.csv", "w", newline="", encoding="utf-8")
customers_file = open("data/recent_customers.csv", "w", newline="", encoding="utf-8")
products_file = open("data/recent_products.csv", "w", newline="", encoding="utf-8")
features_file = open("data/recent_features.csv", "w", newline="", encoding="utf-8")
payments_file = open("data/recent_payments.csv", "w", newline="", encoding="utf-8")

# Writers
orders_writer = None
customers_writer = None
products_writer = None
features_writer = None
payments_writer = None

# ---- Configuration ---- #
# You may set this to None to fallback to last 24h
USE_MIN_UPDATE_DATE = True

# Only one of these should be used per API rules
minimum_update_date = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
minimum_id = None  # e.g., 160000000 or leave None to default to last 24h
statuses = "Ordered,OnDelivery"  # optional

# ---- Pagination ---- #
page = 1
total_saved = 0
MAX_PER_PAGE = 100

while True:
    params = {"page": page}

    # Choose either min date or ID — not both!
    if USE_MIN_UPDATE_DATE and minimum_update_date:
        params["minimumUpdateDate"] = minimum_update_date
    elif minimum_id:
        params["minimumId"] = minimum_id

    if statuses:
        params["status"] = statuses

    response = requests.get(URL, headers=HEADERS, params=params)
    print(f"🔄 Page {page} - Status Code: {response.status_code}")

    if response.status_code != 200:
        print("❌ Error:", response.text)
        break

    data = response.json()
    orders = data.get("data", [])
    if not orders:
        print("⚠️ No orders found.")
        break

    for order in orders:
        # Orders table
        order_row = {
            "id": order.get("id"),
            "waiterName": order.get("waiterName"),
            "deliveryUserName": order.get("deliveryUserName"),
            "externalAppName": order.get("externalAppName"),
            "orderTotal": order.get("orderTotal"),
            "paymentMethodName": order.get("paymentMethodName"),
            "paymentMethodId": order.get("paymentMethodId"),
            "deliveryTime": order.get("deliveryTime"),
            "discountAmount": order.get("discountAmount"),
            "currency": order.get("currency"),
            "confirmationCode": order.get("confirmationCode"),
            "status": order.get("status"),
            "updateDate": order.get("updateDate"),
            "addressId": order.get("addressId"),
            "restaurantKey": order.get("restaurantKey"),
            "deliveryType": order.get("deliveryType"),
            "scheduledTime": order.get("scheduledTime"),
            "isScheduledOrder": order.get("isScheduledOrder"),
            "customerLatitude": order.get("customerLatitude"),
            "customerLongitude": order.get("customerLongitude")
        }
        if not orders_writer:
            orders_writer = csv.DictWriter(orders_file, fieldnames=order_row.keys())
            orders_writer.writeheader()
        orders_writer.writerow(order_row)

        # Customers table
        customer = order.get("customer")
        if customer:
            customer_row = {
                "orderId": order.get("id"),
                "customerName": customer.get("customerName"),
                "customerPhone": customer.get("customerPhone"),
                "region": customer.get("region"),
                "address": customer.get("address"),
                "addressDescription": customer.get("addressDescription"),
                "addressHeader": customer.get("addressHeader")
            }
            if not customers_writer:
                customers_writer = csv.DictWriter(customers_file, fieldnames=customer_row.keys())
                customers_writer.writeheader()
            customers_writer.writerow(customer_row)

        # Products table
        for p in order.get("products", []):
            product_row = {
                "orderId": order.get("id"),
                "productName": p.get("productName"),
                "quantity": p.get("quantity"),
                "unitPrice": p.get("unitPrice"),
                "totalAmount": p.get("totalAmount"),
                "productId": p.get("productId"),
                "productUnitId": p.get("productUnitId"),
                "description": p.get("description")
            }
            if not products_writer:
                products_writer = csv.DictWriter(products_file, fieldnames=product_row.keys())
                products_writer.writeheader()
            products_writer.writerow(product_row)

            # Features table
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

        # Payments table
        for pay in order.get("payments", []):
            payment_row = {
                "orderId": pay.get("orderId"),
                "paymentName": pay.get("paymentName"),
                "amount": pay.get("amount"),
                "currency": pay.get("currency"),
                "exchangeRate": pay.get("exchangeRate"),
                "insertDate": pay.get("insertDate")
            }
            if not payments_writer:
                payments_writer = csv.DictWriter(payments_file, fieldnames=payment_row.keys())
                payments_writer.writeheader()
            payments_writer.writerow(payment_row)

        total_saved += 1

    # Pagination
    if page >= data.get("pageCount", 1):
        break

    page += 1
    print("⏳ Waiting 45 sec before next page...")
    time.sleep(45)

# Close files
orders_file.close()
customers_file.close()
products_file.close()
features_file.close()
payments_file.close()

print(f"✅ Finished. Total orders saved: {total_saved}")
