import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="TableWise Dashboard", layout="wide")

# ---- Load data ----
@st.cache_data

def load_data():
    orders = pd.read_csv("data/orders.csv")
    products = pd.read_csv("data/products.csv")
    features = pd.read_csv("data/features.csv")

    orders.columns = orders.columns.str.strip().str.lower().str.replace(" ", "_")
    orders["insertdate"] = pd.to_datetime(orders["insertdate"], format='mixed')

    products.columns = products.columns.str.strip().str.lower().str.replace(" ", "_")
    features.columns = features.columns.str.strip().str.lower().str.replace(" ", "_")

    return orders, products, features

orders, products, features = load_data()

# ---- Sidebar Filters ----
st.sidebar.header("Filters")
min_date, max_date = orders["insertdate"].min(), orders["insertdate"].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

branches = st.sidebar.multiselect("Select Table", orders["tablename"].dropna().unique(), default=None)
channels = st.sidebar.multiselect("Select Channel", orders["saleschannelname"].dropna().unique(), default=None)

# ---- Filter Data ----
mask = (orders["insertdate"].dt.date >= date_range[0]) & (orders["insertdate"].dt.date <= date_range[1])
if branches:
    mask &= orders["tablename"].isin(branches)
if channels:
    mask &= orders["saleschannelname"].isin(channels)

filtered_orders = orders[mask]

# ---- KPIs ----
total_sales = filtered_orders["ordertotal"].sum()
total_transactions = filtered_orders["id"].nunique()
total_customers = filtered_orders["customerid"].nunique()
avg_basket = total_sales / total_transactions if total_transactions else 0

# ---- Layout ----
st.title("Sales Insights")
st.markdown("### Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Sales", f"{total_sales:,.0f} ₺")
col2.metric("📦 Transactions", total_transactions)
col3.metric("🢁 Customers", total_customers)
col4.metric("🛒 Avg Basket", f"{avg_basket:,.2f} ₺")

st.markdown("---")

# ---- Pie Charts ----
pie1, pie2 = st.columns(2)

with pie1:
    by_table = filtered_orders.groupby("tablename")["ordertotal"].sum().reset_index()
    fig = px.pie(by_table, values="ordertotal", names="tablename", title="Table Sales")
    st.plotly_chart(fig, use_container_width=True)

with pie2:
    by_channel = filtered_orders.groupby("saleschannelname")["ordertotal"].sum().reset_index()
    fig = px.pie(by_channel, values="ordertotal", names="saleschannelname", title="Sales by Channel")
    st.plotly_chart(fig, use_container_width=True)

st.title("Menu Insights")
st.markdown("### Product Performance Metrics")

product_counts = products["productname"].nunique()
distinct_customizations = features["featurename"].nunique()
avg_contribution_margin = (products["totalamount"] - products["quantity"] * products["unitprice"]).mean()
potential_food_cost = 0  # Placeholder unless you have cost column

col1, col2, col3, col4 = st.columns(4)
col1.metric("Number of Menu Items", product_counts)
col2.metric("Distinct Customizations", distinct_customizations)
col3.metric("Avg Contribution Margin", f"{avg_contribution_margin:.2f} ₺")
col4.metric("Potential Food Cost %", f"{potential_food_cost:.2f}%")

# ---- Order Type Breakdown ----
col5, col6 = st.columns(2)

with col5:
    order_types = filtered_orders.groupby("ordertype")["ordertotal"].sum().reset_index()
    fig = px.pie(order_types, values="ordertotal", names="ordertype", title="Order Types")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    top_features = features["featurename"].value_counts().head(10).reset_index()
    top_features.columns = ["Feature", "Count"]
    fig = px.bar(top_features, x="Feature", y="Count", title="Top Customizations")
    st.plotly_chart(fig, use_container_width=True)

# ---- Top Products Table ----
st.markdown("### 🏆 Top Products")
top_products = (
    products.groupby("productname")
    .agg(
        total_sales=("totalamount", "sum"),
        avg_price=("unitprice", "mean"),
        count=("quantity", "sum")
    )
    .sort_values("total_sales", ascending=False)
    .reset_index()
)

st.dataframe(top_products.head(15), use_container_width=True)

# ---- Product Cluster Analysis ----
st.markdown("### Product Cluster Analysis")
# Calculate estimated cost as 80% of unit price (adjust as needed)
products["estimated_cost"] = products["unitprice"] * 0.8

product_perf = (
    products.groupby("productname")
    .agg(
        popularity=("quantity", "sum"),
        total_revenue=("totalamount", "sum"),
        total_cost=("estimated_cost", "sum"),
        avg_price=("unitprice", "mean")
    )
    .reset_index()
)

# Avoid division by zero
product_perf = product_perf[product_perf["popularity"] > 0]

# Profitability = margin per item
product_perf["profitability"] = (product_perf["total_revenue"] - product_perf["total_cost"]) / product_perf["popularity"]

# Add margin and size
product_perf["margin_total"] = product_perf["total_revenue"] - product_perf["total_cost"]
product_perf["bubble_size"] = product_perf["margin_total"].clip(lower=0)

fig = px.scatter(
    product_perf,
    x="profitability",
    y="popularity",
    size="bubble_size",
    color="productname",
    hover_data=["productname", "total_revenue", "popularity", "profitability", "margin_total"],
    title="Product Cluster Analysis"
)
st.plotly_chart(fig, use_container_width=True)

# ---- Cohort Analysis & Retention ----

# Prepare cohort dataset
orders["order_month"] = orders["insertdate"].dt.to_period("M")
orders["cohort_month"] = orders.groupby("customerid")["insertdate"].transform("min").dt.to_period("M")

cohort_data = (
    orders.groupby(["cohort_month", "order_month"])
    .agg(n_customers=("customerid", "nunique"))
    .reset_index()
)

# Calculate period number
cohort_data["cohort_index"] = (cohort_data["order_month"] - cohort_data["cohort_month"]).apply(lambda x: x.n)

# Pivot table
cohort_pivot = cohort_data.pivot_table(index="cohort_month", columns="cohort_index", values="n_customers")

# ---- Visualize ----
st.markdown("### 👥 Customer Cohort Analysis")
fig, ax = plt.subplots(figsize=(15, 6))
sns.heatmap(cohort_pivot, annot=True, fmt=".0f", cmap="YlOrBr", ax=ax)
st.pyplot(fig)

orders["insert_month"] = orders["insertdate"].dt.to_period("M")
orders["first_order_month"] = orders.groupby("customerid")["insertdate"].transform("min").dt.to_period("M")

cohort = (
    orders.groupby(["first_order_month", "insert_month"])["customerid"]
    .nunique()
    .reset_index()
    .rename(columns={"customerid": "customers"})
)

# ---- Weekday Analysis ----

orders["weekday"] = orders["insertdate"].dt.day_name()
orders["branch"] = orders["tablename"].fillna("Unknown")  # or however you identify branches
weekday_sales = (
    orders.groupby(["branch", "weekday"])["ordertotal"]
    .agg(["sum", "count"])
    .reset_index()
    .rename(columns={"sum": "total_sales", "count": "num_orders"})
)
total_per_branch = weekday_sales.groupby("branch")["total_sales"].transform("sum")
weekday_sales["pct_of_branch"] = weekday_sales["total_sales"] / total_per_branch * 100

pivot = weekday_sales.pivot(index="branch", columns="weekday", values="pct_of_branch").fillna(0)
pivot = pivot[["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]  # Order weekdays

st.subheader("📆 Branch Sales Distribution by Weekday")

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(pivot, annot=True, fmt=".1f", cmap="coolwarm", cbar_kws={"label": "% of Weekly Sales"})
st.pyplot(fig)

# --- Costs ---
@st.cache_data
def load_product_cost_data():
    products = pd.read_csv("data/products.csv")
    costs = pd.read_excel("data/costs.xlsx", sheet_name="Costs")

    # Normalize product names for merging
    products['normalized_name'] = products['productName'].str.strip().str.lower()
    costs['normalized_name'] = costs['Product'].str.strip().str.lower()

    # Merge cost info
    df = pd.merge(products, costs[['Cost', 'normalized_name']], on='normalized_name', how='left')
    return df

products_df = load_product_cost_data()

# --- Calculate Profitability Fields ---
commission_rate = 0.13  # 13% default platform fee

def calculate_profit_table(df):
    df = df.copy()

    # Fill missing costs with zero
    df["Cost"] = df["Cost"].fillna(0)

    # Calculate basic totals
    df["toplam_satis"] = df["unitPrice"] * df["quantity"]
    df["bugunku_komisyon"] = df["toplam_satis"] * commission_rate
    df["bugunku_urun_maliyeti"] = df["Cost"] * df["quantity"]

    # Assume these are zero for now (could be loaded later)
    df["genel_gider_maliyeti"] = 0.0
    df["servis_maliyeti"] = 0.0
    df["paketleme_maliyeti"] = 0.0

    # Per unit breakdowns
    df["komisyon_birim"] = df["unitPrice"] * commission_rate
    df["urun_maliyet_birim"] = df["Cost"]
    df["genel_gider_birim"] = 0.0
    df["servis_birim"] = 0.0
    df["paketleme_birim"] = 0.0

    # Total unit cost
    df["toplam_maliyet_birim"] = df[
        ["komisyon_birim", "urun_maliyet_birim", "genel_gider_birim", "servis_birim", "paketleme_birim"]
    ].sum(axis=1)

    # Total cost = unit * quantity
    df["toplam_maliyet"] = df["toplam_maliyet_birim"] * df["quantity"]

    # Profit
    df["kar"] = df["toplam_satis"] - df["toplam_maliyet"]
    df["birim_kazanc"] = df["unitPrice"] - df["toplam_maliyet_birim"]
    df["kar_orani"] = (df["birim_kazanc"] / df["unitPrice"]).fillna(0) * 100

    # Final display
    df_result = df[[
        "orderId", "productName", "quantity", "unitPrice", "toplam_satis",
        "bugunku_komisyon", "bugunku_urun_maliyeti", "komisyon_birim", "urun_maliyet_birim",
        "toplam_maliyet_birim", "toplam_maliyet", "birim_kazanc", "kar_orani"
    ]]

    df_result.rename(columns={
        "orderId": "Order ID",
        "productName": "Product",
        "quantity": "Qty",
        "unitPrice": "Unit Price",
        "toplam_satis": "Total Sales",
        "bugunku_komisyon": "Commission (Total)",
        "bugunku_urun_maliyeti": "Cost (Total)",
        "komisyon_birim": "Commission/unit",
        "urun_maliyet_birim": "Cost/unit",
        "toplam_maliyet_birim": "Total Cost/unit",
        "toplam_maliyet": "Total Cost",
        "birim_kazanc": "Profit/unit",
        "kar_orani": "Profit Margin %"
    }, inplace=True)

    return df_result

profit_table = calculate_profit_table(products_df)

# --- Cost Visual ---
st.title("💰 Product Cost & Profitability Analysis")
st.dataframe(profit_table.head(15).style.format({
    "Unit Price": "₺{:.2f}",
    "Total Sales": "₺{:.2f}",
    "Commission (Total)": "₺{:.2f}",
    "Cost (Total)": "₺{:.2f}",
    "Commission/unit": "₺{:.2f}",
    "Cost/unit": "₺{:.2f}",
    "Total Cost/unit": "₺{:.2f}",
    "Total Cost": "₺{:.2f}",
    "Profit/unit": "₺{:.2f}",
    "Profit Margin %": "{:.2f}%"
}), use_container_width=True)
