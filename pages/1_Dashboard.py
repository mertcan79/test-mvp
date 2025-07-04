import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from collections import Counter

st.set_page_config(page_title="UseydIntel TR", layout="wide")
menu = pd.read_csv("data/menu.csv")
orders = pd.read_csv("data/orders.csv", parse_dates=["datetime"])
inventory = pd.read_csv("data/inventory.csv")

st.title("📈 Restaurant Dashboard")

# Sidebar filters
date_range = st.sidebar.date_input("Date range", [orders.datetime.min(), orders.datetime.max()])
menu_cat = st.sidebar.multiselect("Categories", sorted(menu.category.unique()), default=menu.category.unique())

# Filtered data
start_datetime = pd.to_datetime(date_range[0])
end_datetime = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

o = orders[orders["datetime"].between(start_datetime, end_datetime)]
o = o[o["items"].str.contains('|'.join(menu[menu["category"].isin(menu_cat)]["item_id"].astype(str)))]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders", len(o))
col2.metric("Total Revenue", f"{o.total_price.sum():.2f} TL")
col3.metric("Avg Order Value", f"{o.total_price.mean():.2f} TL")

top_items = pd.Series([it['item_id'] for row in o["items"] for it in ast.literal_eval(row)]).value_counts().head(3)
col4.metric("Top 3 Items", ", ".join(menu.set_index("item_id").loc[top_items.index]["item_name"]))

# Charts
st.line_chart(o.set_index("datetime").resample("D").sum()["total_price"])

# Top items chart
item_counts = pd.Series([it['item_id'] for row in o["items"] for it in ast.literal_eval(row)]).value_counts()
top = menu.set_index("item_id").loc[item_counts.index].assign(count=item_counts.values)
st.bar_chart(top[['item_name', 'count']].set_index('item_name'))

# Inventory
st.subheader("Inventory Status")
st.dataframe(inventory)
low_stock = inventory[inventory.stock_qty_kg <= inventory.restock_threshold_kg]
if not low_stock.empty:
    st.warning("⚠️ Low stock alert:")
    st.dataframe(low_stock)

# Orders table
st.subheader("Recent Orders")
st.dataframe(o.sort_values("datetime", ascending=False).head(10))
