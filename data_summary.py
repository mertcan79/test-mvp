import pandas as pd
import ast
from collections import Counter
from datetime import timedelta

def generate_data_summary(order_path="data/orders.csv", menu_path="data/menu.csv", inventory_path="data/inventory.csv"):
    # Load data
    orders = pd.read_csv(order_path, parse_dates=["datetime"])
    menu = pd.read_csv(menu_path)
    inventory = pd.read_csv(inventory_path)

    # Ensure correct types
    orders["datetime"] = pd.to_datetime(orders["datetime"])
    menu["item_id"] = menu["item_id"].astype(int)

    # Add day field
    orders["date"] = orders["datetime"].dt.date

    # === Flatten Order Items ===
    item_records = []
    for _, row in orders.iterrows():
        try:
            items = ast.literal_eval(row["items"])
            for i in items:
                item_records.append({
                    "date": row["date"],
                    "item_id": i["item_id"],
                    "quantity": i["quantity"]
                })
        except Exception:
            continue

    item_df = pd.DataFrame(item_records)
    item_df = item_df.groupby(["date", "item_id"]).sum().reset_index()

    # Merge with menu
    item_df = item_df.merge(menu[["item_id", "item_name", "category"]], on="item_id", how="left")

    # Get 14-day item trends
    recent_dates = sorted(item_df["date"].unique())[-14:]
    trend_lines = []
    for item_id in item_df["item_id"].unique():
        item_name = item_df[item_df["item_id"] == item_id]["item_name"].iloc[0]
        category = item_df[item_df["item_id"] == item_id]["category"].iloc[0]
        daily_qty = item_df[item_df["item_id"] == item_id].set_index("date")["quantity"]
        trend = [int(daily_qty.get(date, 0)) for date in recent_dates]
        trend_lines.append(f"- {item_name} (category: {category}) sales trend (last 14 days): {trend}")

    # Revenue summary
    total_rev = orders["total_price"].sum()
    avg_order = orders["total_price"].mean()

    # Day-of-week performance
    orders["day_name"] = orders["datetime"].dt.day_name()
    dow_avg = orders.groupby("day_name")["total_price"].mean().sort_values()
    low_day = dow_avg.idxmin()
    low_val = dow_avg.min()

    # Low stock
    low_stock_items = inventory[inventory["stock_qty_kg"] < inventory["restock_threshold_kg"]]["ingredient"].tolist()

    # Final summary
    summary = f"""
In the last 30 days, total revenue was {total_rev:.2f} TL and average order value was {avg_order:.2f} TL.
The slowest day for orders is {low_day}, with average order value of {low_val:.2f} TL.

Low-stock ingredients: {', '.join(low_stock_items) if low_stock_items else 'None'}.

Here are sales trends for key items over the last 14 days:
{chr(10).join(trend_lines[:10])}  # Limiting to top 10 for brevity
"""
    return summary
