import os, sys, csv, time, requests, pathlib
from datetime import datetime, timezone
from typing import Dict, List
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# 1. Environment & CLI
# ----------------------------------------------------------------------
load_dotenv()
API_KEY     = os.getenv("adisyo_web_siparis")
API_SECRET  = os.getenv("adisyo_api")
CONSUMER    = os.getenv("adisyo_id", "burgerator")

if not (API_KEY and API_SECRET):
    sys.exit("❌  Set ADISYO credentials in .env")

from urllib.parse import quote

start_iso = sys.argv[1] if len(sys.argv) > 1 else "2024-01-10 16:51:19"
encoded_start = quote(start_iso, safe="")                          

BASE_URL   = "https://ext.adisyo.com/api/External/v2/CompletedOrders"
HEADERS    = {
    "x-api-key":     API_KEY,
    "x-api-secret":  API_SECRET,
    "x-api-consumer":CONSUMER,
    "accept":        "application/json"
}

OUT_DIR = pathlib.Path("data/historical")
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "orders"   : OUT_DIR / "completed_orders_2.csv",
    "products" : OUT_DIR / "products_2.csv",
    "features" : OUT_DIR / "features_2.csv",
    "payments" : OUT_DIR / "payments_2.csv",
}

WRITERS: Dict[str, csv.DictWriter] = {}

def get_writer(key: str, fieldnames: List[str]) -> csv.DictWriter:
    """
    Lazily open file in append mode; write header once.
    """
    if key in WRITERS:
        return WRITERS[key]

    file_exists = FILES[key].exists()
    f = FILES[key].open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    WRITERS[key] = writer
    return writer

# ----------------------------------------------------------------------
# 2. Fetch loop with paging + retry
# ----------------------------------------------------------------------
def fetch_page(page: int) -> Dict:
    resp = requests.get(
        f"{BASE_URL}?page={page}&startDate={encoded_start}",
        headers=HEADERS,
        timeout=60,
    )
    return resp

page, max_retry, retries = 1, 5, 0
total_orders_written = 0

while True:
    r = fetch_page(page)
    print(f"📄 Page {page}  →  {r.status_code}")

    if r.status_code == 601:                       # Adisyo throttling
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
    orders  = payload.get("orders", [])
    if not orders:
        break

    # ------------------------------------------------------------------
    # write CSV rows
    # ------------------------------------------------------------------
    for o in orders:
        orders_row = {
            "order_id" : o["id"],
            "insertDate": o["insertDate"],
            "updateDate": o["updateDate"],
            "closedDate": o.get("closedDate"),
            "orderTotal": o["orderTotal"],
            "taxAmount" : o["taxAmount"],
            "currency"  : o["currency"],
            "orderType" : o["orderType"],
            "status"    : o["status"],
            "salesChannel": o.get("salesChannelName"),
            "tableName" : o.get("tableName"),
            "orderNumber": o.get("orderNumber"),
            "customerId": o.get("customerId"),
        }
        get_writer("orders", orders_row.keys()).writerow(orders_row)

        # products & nested features
        for p in o.get("products", []):
            prod_row = {
                "order_id"   : o["id"],
                "order_product_id": p["id"],
                "product_id" : p["productId"],
                "productName": p["productName"],
                "quantity"   : p["quantity"],
                "unitPrice"  : p["unitPrice"],
                "totalAmount": p["totalAmount"],
                "category"   : p["categoryName"],
                "isMenu"     : p["isMenu"],
                "parentId"   : p["parentId"],
                "discount"   : p["discountAmount"]
            }
            get_writer("products", prod_row.keys()).writerow(prod_row)

            for f in p.get("features", []):
                feat_row = {
                    "order_product_id": p["id"],
                    "feature_id" : f["featureId"],
                    "featureName": f["featureName"],
                    "additionalPrice": f["additionalPrice"]
                }
                get_writer("features", feat_row.keys()).writerow(feat_row)

        # payments
        for pay in o.get("payments", []):
            pay_row = {
                "order_id"      : o["id"],
                "paymentTypeId" : pay["paymentTypeId"],
                "paymentName"   : pay["paymentName"],
                "amount"        : pay["amount"],
                "currency"      : pay["currency"],
                "insertDate"    : pay["insertDate"]
            }
            get_writer("payments", pay_row.keys()).writerow(pay_row)

        total_orders_written += 1

    # flush every page so nothing is lost
    for w in WRITERS.values():
        w.writerows([])          # triggers flush on underlying file

    if page >= payload.get("pageCount", page):
        break

    page += 1
    time.sleep(50)               # be kind to the API

# ----------------------------------------------------------------------
# 3. Cleanup
# ----------------------------------------------------------------------
for writer in WRITERS.values():
    writer = writer  # noqa
    writer.writerow({})          # ensure final flush
print(f"✅  Finished. {total_orders_written} orders saved to CSVs.")
