import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import re
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
st.set_page_config(page_title="TableWise Dashboard", layout="wide")

# ---- Load data ----
@st.cache_data
def load_data():
    orders = pd.read_csv("data/full/orders.csv")
    products = pd.read_csv("data/full/products.csv")
    features = pd.read_csv("data/full/features.csv")
    payments = pd.read_csv("data/full/payments.csv")

    # Clean columns
    for df in [orders, products, features, payments]:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    
    # Parse dates
    orders["insertdate"] = pd.to_datetime(orders["insertdate"], format='mixed')
    payments["insertdate"] = pd.to_datetime(payments["insertdate"], format='mixed')

    # Use only first payment per order (or customize to sum by orderId if needed)
    payment_map = payments.groupby("orderid")["paymentname"].first().reset_index()
    orders = orders.merge(payment_map, left_on="id", right_on="orderid", how="left")
    orders.drop(columns=["orderid"], inplace=True)

    return orders, products, features, payments

orders, products, features, payments = load_data()

# ---- Sidebar Filters ----
st.sidebar.header("Filters")
min_date, max_date = orders["insertdate"].min(), orders["insertdate"].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

branches = st.sidebar.multiselect("Select Table", orders["tablename"].dropna().unique(), default=None)
channel_types = st.sidebar.multiselect("Select Payment Channel", orders["paymentname"].dropna().unique())

# ---- Filter Data ----
mask = (orders["insertdate"].dt.date >= date_range[0]) & (orders["insertdate"].dt.date <= date_range[1])
if branches:
    mask &= orders["tablename"].isin(branches)
if channel_types:
    mask &= orders["paymentname"].isin(channel_types)

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
    by_payment = filtered_orders.groupby("paymentname")["ordertotal"].sum().reset_index()
    fig = px.pie(by_payment, values="ordertotal", names="paymentname", title="Sales by Payment Channel")
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

# ---- Profitability ----@st.cache_data

def load_product_cost_data():
    products = pd.read_csv("data/full/products.csv")
    raw_costs = pd.read_excel("data/full/costs.xlsx", sheet_name="Costs")

    # Clean function for product names
    def clean_name(name):
        if pd.isna(name):
            return ''
        name = str(name).lower().strip()
        name = re.sub(r"\(.*?\)", "", name)
        name = re.sub(r"\d+\s?(g|gr|ml|cl)", "", name)
        name = re.sub(r"[^a-zçğıöşü\s]", "", name)
        name = re.sub(r"\s+", " ", name).strip()
        return name

    # Prepare clean cost table from the finalized format
    raw_costs.columns = raw_costs.columns.str.strip()
    raw_costs['normalized_name'] = raw_costs['Product'].apply(clean_name)
    costs = raw_costs.groupby('normalized_name', as_index=False).agg({'Cost': 'mean'})

    products['normalized_name'] = products['productName'].apply(clean_name)

    canonical_map = products.groupby('normalized_name')['productName'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
    products['productName'] = products['normalized_name'].map(canonical_map)

    df = pd.merge(products, costs, on='normalized_name', how='left')

    exclude_keywords = [
        "istemiyorum", "pişmiş", "seçimi", "not", "sıfır", "adet",
        "ayran", "coca", "fanta", "ice tea", "şeftali", "vişne", "sos", "extra",
        "ketçap", "mayonez", "su", "çay", "çubuk", "mozzarella", "patates", "ball", "stick", "cola"
    ]
    df = df[~df["productName"].str.lower().str.contains('|'.join(exclude_keywords))]
    df = df[df["unitPrice"] > 0]

    return df

products_df = load_product_cost_data()

# --- Calculate Profitability Fields ---
commission_rate = 0.13

def calculate_profit_table(df):
    df = df.copy()

    df["toplam_satis"] = df["unitPrice"] * df["quantity"]
    df["bugunku_komisyon"] = df["toplam_satis"] * commission_rate
    df["bugunku_urun_maliyeti"] = df["Cost"] * df["quantity"]

    df["genel_gider_maliyeti"] = 0.0
    df["servis_maliyeti"] = 0.0
    df["paketleme_maliyeti"] = 0.0

    df["komisyon_birim"] = df["unitPrice"] * commission_rate
    df["urun_maliyet_birim"] = df["Cost"]
    df["genel_gider_birim"] = 0.0
    df["servis_birim"] = 0.0
    df["paketleme_birim"] = 0.0

    df["toplam_maliyet_birim"] = df[["komisyon_birim", "urun_maliyet_birim", "genel_gider_birim", "servis_birim", "paketleme_birim"]].sum(axis=1)
    df["toplam_maliyet"] = df["toplam_maliyet_birim"] * df["quantity"]
    df["kar"] = df["toplam_satis"] - df["toplam_maliyet"]
    df["birim_kazanc"] = df["unitPrice"] - df["toplam_maliyet_birim"]
    df["kar_orani"] = (df["birim_kazanc"] / df["unitPrice"]).fillna(0) * 100

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

# --- Streamlit Display ---
st.title("💰 Product Cost & Profitability Analysis")

view_option = st.radio("View Mode", ["Detailed (Raw)", "Summarized (By Product)"])

if view_option == "Summarized (By Product)":
    summary = (
        profit_table.groupby("Product")
        .agg({
            "Qty": "sum",
            "Unit Price": "mean",
            "Total Sales": "sum",
            "Commission (Total)": "sum",
            "Cost (Total)": "sum",
            "Total Cost": "sum",
            "Profit/unit": "mean",
            "Profit Margin %": "mean"
        })
        .reset_index()
    )
    st.dataframe(summary.style.format({
        "Unit Price": "₺{:.2f}",
        "Total Sales": "₺{:.2f}",
        "Commission (Total)": "₺{:.2f}",
        "Cost (Total)": "₺{:.2f}",
        "Total Cost": "₺{:.2f}",
        "Profit/unit": "₺{:.2f}",
        "Profit Margin %": "{:.2f}%"
    }), use_container_width=True)
else:
    st.dataframe(profit_table.head(50).style.format({
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
