import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="TableWise", layout="wide")

# ---- Load data ----
@st.cache_data
def load_data():
    df = pd.read_csv("data/adisyo_completed_orders_full_195d.csv")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["insert_date"] = pd.to_datetime(df["insert_date"], format='mixed')
    return df

df = load_data()

# ---- Sidebar Filters ----
st.sidebar.header("Filters")
min_date, max_date = df["insert_date"].min(), df["insert_date"].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

branches = st.sidebar.multiselect("Select Branch", df["table"].dropna().unique(), default=None)
channels = st.sidebar.multiselect("Select Channel", df["status"].unique(), default=None)

# ---- Filter Data ----
mask = (df["insert_date"].dt.date >= date_range[0]) & (df["insert_date"].dt.date <= date_range[1])
if branches:
    mask &= df["table"].isin(branches)
if channels:
    mask &= df["status"].isin(channels)

filtered_df = df[mask]

# ---- KPIs ----
total_sales = filtered_df["total_product_price"].sum()
total_transactions = filtered_df["order_id"].nunique()
total_customers = filtered_df["order_id"].nunique()  
avg_basket = total_sales / total_transactions if total_transactions else 0

# ---- Layout ----
st.title("Sales Insights")
st.markdown("### Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Sales", f"{total_sales:,.0f} ₺")
col2.metric("📦 Transactions", total_transactions)
col3.metric("🧑 Customers", total_customers)
col4.metric("🛒 Avg Basket", f"{avg_basket:,.2f} ₺")

st.markdown("---")

# ---- Pie Charts ----
pie1, pie2 = st.columns(2)

with pie1:
    by_branch = filtered_df.groupby("table")["total_product_price"].sum().reset_index()
    fig = px.pie(by_branch, values="total_product_price", names="table", title="Branch Sales")
    st.plotly_chart(fig, use_container_width=True)

with pie2:
    by_channel = filtered_df.groupby("status")["total_product_price"].sum().reset_index()
    fig = px.pie(by_channel, values="total_product_price", names="status", title="Sales by Status")
    st.plotly_chart(fig, use_container_width=True)

# ---- More Pie Charts ----
col5, col6 = st.columns(2)

with col5:
    order_types = filtered_df.groupby("order_type")["total_product_price"].sum().reset_index()
    fig = px.pie(order_types, values="total_product_price", names="order_type", title="Order Types")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    categories = filtered_df["product"].str.extract(r'(?P<category>\w+)')
    df_cat = pd.concat([filtered_df, categories], axis=1)
    by_category = df_cat.groupby("category")["total_product_price"].sum().reset_index()
    fig = px.pie(by_category, values="total_product_price", names="category", title="Categories")
    st.plotly_chart(fig, use_container_width=True)

# ---- Top Products Table ----
st.markdown("### 🏆 Top Products")
top_products = (
    filtered_df.groupby("product")
    .agg(
        total_sales=("total_product_price", "sum"),
        avg_price=("unit_price", "mean"),
        count=("quantity", "sum")
    )
    .sort_values("total_sales", ascending=False)
    .reset_index()
)

st.dataframe(top_products.head(15), use_container_width=True)

