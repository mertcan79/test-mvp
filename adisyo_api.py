import os
import requests
import pandas as pd

BASE_URL = "https://api.adisyo.com/v1"  # adjust based on Postman collection
API_KEY = os.getenv("ADISYO_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

SAVE_DIR = "data"
os.makedirs(SAVE_DIR, exist_ok=True)

def fetch_menu():
    resp = requests.get(f"{BASE_URL}/menu", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("items", [])

def fetch_orders(start_date=None, end_date=None):
    params = {}
    if start_date:
        params["dateFrom"] = start_date
    if end_date:
        params["dateTo"] = end_date
    resp = requests.get(f"{BASE_URL}/orders", headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json().get("orders", [])

def fetch_inventory():
    resp = requests.get(f"{BASE_URL}/stock", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("stockItems", [])

def save_to_csv(data, filename):
    df = pd.json_normalize(data)
    df.to_csv(os.path.join(SAVE_DIR, filename), index=False)
    print(f"Saved {filename}")

def main():
    menu = fetch_menu()
    save_to_csv(menu, "menu_from_adisyo.csv")

    orders = fetch_orders(start_date="2025-06-01", end_date="2025-07-04")
    save_to_csv(orders, "orders_from_adisyo.csv")

    stock = fetch_inventory()
    save_to_csv(stock, "inventory_from_adisyo.csv")

if __name__ == "__main__":
    print("▶️ Run locally after setting ADISYO_API_KEY")
