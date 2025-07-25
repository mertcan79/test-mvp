# streamlit_dashboard_recent.py
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests
from PIL import Image

# Load and display logo
logo = Image.open("archive/logo.png")
st.image(logo, width=150)
st.markdown(
    """
    <style>
    .main {
        background-color: #f7f8ff;
    }
    .css-18e3th9 {
        background-color: #f7f8ff;
    }
    .stApp {
        color: #333;
    }
    .st-bw {
        color: #2E2EFF;  /* Use logo blue color for primary text */
    }
    .css-1d391kg {
        background-color: #2E2EFF !important;  /* logo purple */
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="Recent Orders Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/adisyo_recent_orders.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["insert_date"] = pd.to_datetime(df["insert_date"], errors="coerce")
    df["delivery_time"] = pd.to_datetime(df["delivery_time"], errors="coerce")
    df["hour"] = df["insert_date"].dt.hour

    def map_time_of_day(hour):
        if 6 <= hour < 11:
            return "Breakfast"
        elif 11 <= hour < 16:
            return "Lunch"
        elif 16 <= hour < 22:
            return "Dinner"
        else:
            return "Late Night"

    df["time_of_day"] = df["hour"].apply(map_time_of_day)

    def extract_district(region):
        if pd.isna(region):
            return None
        region = str(region).lower()
        known_districts = [
            "bağcılar", "bahçelievler", "bakırköy", "zeytinburnu", "fatih", "esenler", "bayrampaşa"
        ]
        for district in known_districts:
            if district in region:
                return district.capitalize()
        return "Diğer"

    df["district"] = df["region"].apply(extract_district)

    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filters")
min_date = df["insert_date"].min().date()
max_date = df["insert_date"].max().date()
date_range = st.sidebar.date_input("Order Date Range", [min_date, max_date])

apps = st.sidebar.multiselect("Delivery App", df["delivery_app"].dropna().unique())
payments = st.sidebar.multiselect("Payment Method", df["payment_method"].dropna().unique())
regions = st.sidebar.multiselect("Region", df["region"].dropna().unique())

# Apply filters
mask = df["insert_date"].dt.date.between(date_range[0], date_range[1])
if apps:
    mask &= df["delivery_app"].isin(apps)
if payments:
    mask &= df["payment_method"].isin(payments)
if regions:
    mask &= df["region"].isin(regions)

filtered = df[mask]

# KPIs
st.title("📦 Recent Orders Dashboard")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"{filtered['order_total'].sum():,.2f} ₺")
col2.metric("Total Orders", filtered["order_id"].nunique())
col3.metric("Avg Order Value", f"{filtered['order_total'].mean():,.2f} ₺")
col4.metric("Avg Items per Order", f"{filtered['product_count'].mean():.2f}")

st.markdown("---")

# Pie Charts
col5, col6 = st.columns(2)
with col5:
    fig = px.pie(filtered, values="order_total", names="delivery_app", title="Sales by Delivery App")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    fig = px.pie(filtered, values="order_total", names="payment_method", title="Sales by Payment Method")
    st.plotly_chart(fig, use_container_width=True)

# Bar Chart by Region
region_sales = filtered.groupby("district")["order_total"].sum().sort_values(ascending=False).reset_index()
st.subheader("💸 Sales by district")
fig = px.bar(region_sales, x="order_total", y="district", orientation="h", title="Top district by Sales")
st.plotly_chart(fig, use_container_width=True)

# Time Series
st.subheader("📈 Daily Sales Trend")
daily_sales = filtered.groupby(filtered["insert_date"].dt.date)["order_total"].sum().reset_index()
daily_sales.columns = ["date", "sales"]
fig = px.line(daily_sales, x="date", y="sales", markers=True)
st.plotly_chart(fig, use_container_width=True)

# Raw Data Table
st.markdown("### 🧾 Recent Orders Table")
st.dataframe(filtered[[
    "order_id", "insert_date", "order_total", "delivery_app", "payment_method", "region", "product_count"
]].sort_values("insert_date", ascending=False), use_container_width=True)

# Step 1: Create period columns (keep as Period for math)
df["order_month_period"] = df["insert_date"].dt.to_period("M")
df["cohort_month_period"] = df.groupby("customer_name")["insert_date"].transform("min").dt.to_period("M")

# Step 2: Calculate index from difference
df["cohort_index"] = (df["order_month_period"] - df["cohort_month_period"]).apply(lambda x: x.n)

# Step 3: Convert to string for plotting
df["order_month"] = df["order_month_period"].astype(str)
df["cohort_month"] = df["cohort_month_period"].astype(str)

# Step 4: Build cohort table
cohort_data = (
    df.groupby(["cohort_month", "order_month"])
    .agg(n_customers=("customer_name", "nunique"))
    .reset_index()
)

cohort_data["cohort_index"] = df["cohort_index"]

# Step 5: Pivot and plot
cohort_pivot = cohort_data.pivot_table(index="cohort_month", columns="cohort_index", values="n_customers")

fig = px.imshow(cohort_pivot, text_auto=True, aspect="auto", title="Customer Cohort Analysis")
st.plotly_chart(fig, use_container_width=True)

df["weekday"] = df["insert_date"].dt.day_name()
weekday_sales = (
    df.groupby(["region", "weekday"])["order_total"]
    .agg(["sum", "count"])
    .reset_index()
    .rename(columns={"sum": "total_sales", "count": "num_orders"})
)

weekday_sales["weekday"] = pd.Categorical(weekday_sales["weekday"], categories=[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
], ordered=True)

pivot = weekday_sales.pivot(index="region", columns="weekday", values="total_sales").fillna(0)
fig = px.imshow(pivot, text_auto=".1f", labels=dict(x="Weekday", y="Region", color="₺ Sales"), title="📆 Sales by Region and Weekday")
st.plotly_chart(fig, use_container_width=True)

st.markdown("## 🔍 Extended Insights")

# --- Filter controls ---
st.sidebar.markdown("### Advanced Filters")
selected_status = st.sidebar.multiselect("Order Status", df["status"].dropna().unique())
selected_time_of_day = st.sidebar.multiselect("Time of Day", df["time_of_day"].dropna().unique())
selected_notes = st.sidebar.multiselect("Order Notes Contain", ["order notes", "special instructions", "allergy info"])

# --- Apply filters ---
if selected_status:
    df = df[df["status"].isin(selected_status)]

if selected_time_of_day:
    df = df[df["time_of_day"].isin(selected_time_of_day)]

for keyword in selected_notes:
    flag_col = f"note_contains_{keyword.replace(' ', '_')}"
    df = df[df[flag_col]]

# --- Subheader ---
st.subheader("📍 Sales by City and Region")

# Prepare district sales
district_sales = df.groupby("district")["order_total"].sum().reset_index()

district_sales["district"] = district_sales["district"].str.title()
# Step 3: Load GeoJSON
geo_url = "https://raw.githubusercontent.com/ozanyerli/istanbul-districts-geojson/main/istanbul-districts.json"
istanbul_geo = requests.get(geo_url).json()

def normalize(text):
    if pd.isna(text):
        return ""
    return (str(text)
        .lower()
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ı", "i")
        .replace("ö", "o")
        .replace("ç", "c")
        .strip())

# Normalize district names in both
district_sales["normalized_district"] = district_sales["district"].apply(normalize)

for feature in istanbul_geo["features"]:
    feature["properties"]["normalized_name"] = normalize(feature["properties"]["name"])

# Plot using normalized keys
fig = px.choropleth_mapbox(
    district_sales,
    geojson=istanbul_geo,
    locations="normalized_district",
    featureidkey="properties.normalized_name",
    color="order_total",
    color_continuous_scale="Oranges",
    mapbox_style="carto-positron",
    zoom=9,
    center={"lat": 41.0082, "lon": 28.9784},
    title="🗺️ Istanbul District-Level Sales"
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)