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

from geopy.geocoders import Nominatim
import time

# Cache coordinates to avoid repeated API calls
@st.cache_data(show_spinner=False)
def get_coordinates(districts):
    geolocator = Nominatim(user_agent="useydintel")
    coords = []
    for d in districts:
        try:
            location = geolocator.geocode(f"{d}, Istanbul, Turkey")
            if location:
                coords.append({"location": d, "lat": location.latitude, "lon": location.longitude})
            else:
                coords.append({"location": d, "lat": None, "lon": None})
            time.sleep(1)  # be polite to the API
        except:
            coords.append({"location": d, "lat": None, "lon": None})
    return pd.DataFrame(coords)

# Aggregate total sales by district
district_sales = o.groupby("location")["total_price"].sum().reset_index()
district_coords = get_coordinates(district_sales["location"].unique())
district_sales = district_sales.merge(district_coords, on="location", how="left")
district_sales = district_sales.dropna(subset=["lat", "lon"])

# Show map
st.subheader("🗺️ Sales by Location Map")
fig = px.scatter_mapbox(
    district_sales,
    lat="lat",
    lon="lon",
    size="total_price",
    hover_name="location",
    size_max=40,
    zoom=9,
    mapbox_style="open-street-map",
    title="Sales Volume by District"
)
st.plotly_chart(fig, use_container_width=True)