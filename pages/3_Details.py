import json
import pandas as pd
from datetime import datetime

# === 1. Load JSON file ===
with open("data/mock_adisyo_orders.json", "r", encoding="utf-8") as f:
    data = json.load(f)

orders_data = data["orders"]

orders = []
products = []
payments = []

for order in orders_data:
    orders.append({
        "orderId": order["id"],
        "orderTotal": order["orderTotal"],
        "waiterName": order["waiterName"],
        "salesChannel": order["salesChannelName"],
        "status": order["status"],
        "tableName": order["tableName"],
        "taxAmount": order["taxAmount"],
        "insertDate": order["insertDate"],
        "updateDate": order["updateDate"],
        "orderType": order["orderType"],
        "orderDate": order["insertDate"][:10]
    })

    for product in order["products"]:
        products.append({
            "orderId": order["id"],
            "productName": product["productName"],
            "quantity": product["quantity"],
            "unitPrice": product["unitPrice"],
            "totalAmount": product["totalAmount"],
            "insertDate": product["insertDate"][:10],
            "groupName": product.get("groupName") or "Uncategorized"
        })

    for pay in order["payments"]:
        payments.append({
            "orderId": pay["orderId"],
            "paymentMethod": pay["paymentName"],
            "amount": pay["amount"],
            "insertDate": pay["insertDate"][:10]
        })

# === 2. Create DataFrames ===
orders_df = pd.DataFrame(orders)
products_df = pd.DataFrame(products)
payments_df = pd.DataFrame(payments)

# === 3. Save CSVs ===
orders_df.to_csv("orders.csv", index=False)
products_df.to_csv("products.csv", index=False)
payments_df.to_csv("payments.csv", index=False)

# === 4. Dashboard Metrics ===

# Total Sales
total_sales = orders_df["orderTotal"].sum()

# Total Transitions (i.e., order count)
total_orders = len(orders_df)

# Total Customers (assuming tableName is proxy; can adapt to real field)
total_customers = orders_df["tableName"].nunique()

# Top Basket Size (highest order value)
top_order = orders_df.sort_values("orderTotal", ascending=False).iloc[0]
top_basket_value = top_order["orderTotal"]

# Branch Sales - Simulated using waiterName or tableName if branches not defined
branch_sales = orders_df.groupby("waiterName")["orderTotal"].sum()

# Sales Channels
channel_sales = orders_df.groupby("salesChannel")["orderTotal"].sum()

# Categories from groupName in products
category_sales = products_df.groupby("groupName")["totalAmount"].sum()

# Order Types
order_type_counts = orders_df["orderType"].value_counts()

# Top Products
top_products = products_df.groupby("productName").agg({
    "quantity": "sum",
    "unitPrice": "mean",
    "totalAmount": "sum"
}).sort_values("totalAmount", ascending=False)

# Payment Methods
payment_breakdown = payments_df.groupby("paymentMethod")["amount"].sum()

# Delivery Time Estimate (not real field here, placeholder)
avg_delivery_time_min = 34  # Simulate if not available

# === 5. Print Summary ===
print("✅ Dashboard Summary:")
print(f"Total Sales: ₺{total_sales:,.2f}")
print(f"Total Orders: {total_orders}")
print(f"Total Customers (Tables): {total_customers}")
print(f"Top Basket: ₺{top_basket_value:.2f}")
print(f"Average Delivery Time: {avg_delivery_time_min} min\n")

print("🟢 Branch Sales:\n", branch_sales, "\n")
print("🔵 Sales Channels:\n", channel_sales, "\n")
print("🟠 Order Types:\n", order_type_counts, "\n")
print("🟡 Categories:\n", category_sales, "\n")
print("🔴 Top Products:\n", top_products.head(5), "\n")
print("🟣 Payment Methods:\n", payment_breakdown, "\n")
