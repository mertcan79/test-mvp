import os, sys, csv, time, requests, pathlib
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from urllib.parse import quote
from collections import OrderedDict

# Load environment variables
load_dotenv()
API_KEY     = os.getenv("adisyo_web_siparis")
API_SECRET  = os.getenv("adisyo_api")
CONSUMER    = os.getenv("adisyo_id", "burgerator")

if not (API_KEY and API_SECRET):
    sys.exit("❌  Set ADISYO credentials in .env")

# Set start date
start_iso     = "2025-06-02 00:00:00"
encoded_start = quote(start_iso, safe="")

# Adisyo API setup
BASE_URL   = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
HEADERS    = {
    "x-api-key": API_KEY,
    "x-api-secret": API_SECRET,
    "x-api-consumer": CONSUMER,
    "accept": "application/json"
}

# Output file setup
OUT_DIR = pathlib.Path("data/historical")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "orders"   : OUT_DIR / "completed_orders_2025_4.csv",
    "products" : OUT_DIR / "products_2025_4.csv",
    "features" : OUT_DIR / "features_2025_4.csv",
    "payments" : OUT_DIR / "payments_2025_4.csv",
}

WRITERS: Dict[str, csv.DictWriter] = {}

def get_writer(key: str, fieldnames: List[str]) -> csv.DictWriter:
    if key in WRITERS:
        return WRITERS[key]
    file_exists = FILES[key].exists()
    f = FILES[key].open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    WRITERS[key] = writer
    return writer

# Fetch one page of orders
def fetch_page(page: int) -> Dict:
    url = f"{BASE_URL}?page={page}&startDate={encoded_start}"
    return requests.get(url, headers=HEADERS, timeout=60)

page, max_retry, retries = 1, 5, 0
total_orders_written = 0

while True:
    r = fetch_page(page)
    print(f"📄 Page {page}  →  {r.status_code}")

    if r.status_code == 601:
        retries += 1
        if retries > max_retry:
            print("⚠️  Too many retries; aborting.")
            break
        time.sleep(45)
        continue
    elif r.status_code != 200:
        print("❌  HTTP error:", r.text)
        break

    retries = 0
    payload = r.json()
    orders = payload.get("orders", [])
    if not orders:
        break

    for o in orders:
        # Flatten top-level fields (skip nested)
        row = OrderedDict(
            (k, v) for k, v in o.items()
            if not isinstance(v, (dict, list)) and k != "customer"
        )

        # Flatten customer fields
        customer = o.get("customer")
        if customer and isinstance(customer, dict):
            for k, v in customer.items():
                row[f"customer_{k}"] = v

        # Write order row
        get_writer("orders", row.keys()).writerow(row)

        # Write products
        for p in o.get("products", []):
            prod_row = {
                "order_id": o["id"],
                "order_product_id": p["id"],
                "product_id": p["productId"],
                "productName": p["productName"],
                "quantity": p["quantity"],
                "unitPrice": p["unitPrice"],
                "totalAmount": p["totalAmount"],
                "category": p["categoryName"],
                "isMenu": p["isMenu"],
                "parentId": p["parentId"],
                "discount": p["discountAmount"]
            }
            get_writer("products", prod_row.keys()).writerow(prod_row)

            # Write features
            for f in p.get("features", []):
                feat_row = {
                    "order_product_id": p["id"],
                    "feature_id": f["featureId"],
                    "featureName": f["featureName"],
                    "additionalPrice": f["additionalPrice"]
                }
                get_writer("features", feat_row.keys()).writerow(feat_row)

        # Write payments
        for pay in o.get("payments", []):
            pay_row = {
                "order_id": o["id"],
                "paymentTypeId": pay["paymentTypeId"],
                "paymentName": pay["paymentName"],
                "amount": pay["amount"],
                "currency": pay["currency"],
                "insertDate": pay["insertDate"]
            }
            get_writer("payments", pay_row.keys()).writerow(pay_row)

        total_orders_written += 1

    # Flush files per page
    for w in WRITERS.values():
        w.writerows([])

    if page >= payload.get("pageCount", page):
        break

    page += 1
    time.sleep(61)

# Final flush
for writer in WRITERS.values():
    writer.writerow({})
print(f"✅  Finished. {total_orders_written} orders saved to CSVs.")
