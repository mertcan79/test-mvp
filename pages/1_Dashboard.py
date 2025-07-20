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

# --- Load Ingredient Costs ---
def load_costs_from_hierarchical_excel(path="data/Burgerator.xlsx", sheet_name="Urun_Maliyet"):
    df = pd.read_excel(path, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()

    # Carry down main product name for ingredients
    df["ÜRÜN"] = df["ÜRÜN"].fillna(method="ffill")
    df["Birim Fiyat"] = pd.to_numeric(df["Birim Fiyat"].replace("₺", "", regex=True), errors="coerce").fillna(0)

    # Total ingredient cost per product
    cost_df = df.groupby("ÜRÜN")["Birim Fiyat"].sum().reset_index()
    cost_df = cost_df.rename(columns={"ÜRÜN": "product", "Birim Fiyat": "unit_cost"})
    cost_df["product"] = cost_df["product"].str.strip().str.lower()
    return cost_df

# --- Prepare Orders ---
def prepare_orders(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["product"] = df["product"].str.strip().str.lower()
    df["tarih"] = pd.to_datetime(df["insert_date"]).dt.date
    df["total_price"] = df["unit_price"] * df["quantity"]
    return df

# --- Merge & Compute Profitability ---
def compute_profitability(orders_df, cost_df):
    merged = pd.merge(orders_df, cost_df, on="product", how="left")
    merged["unit_cost"] = merged["unit_cost"].fillna(0)
    merged["total_cost"] = merged["unit_cost"] * merged["quantity"]
    merged["profit"] = merged["total_price"] - merged["total_cost"]
    merged["profit_margin"] = ((merged["profit"] / merged["total_price"]).fillna(0) * 100).round(2)
    return merged

# --- Load, Process, Display ---
ingredient_costs = load_costs_from_hierarchical_excel()
filtered_df = prepare_orders(filtered_df)
profit_df = compute_profitability(filtered_df, ingredient_costs)

# --- Streamlit Output ---
st.markdown("### 🍔 Ingredient-Based Profitability")

st.dataframe(profit_df[[
    "tarih", "product", "quantity", "unit_price", "total_price",
    "unit_cost", "total_cost", "profit", "profit_margin"
]].sort_values("profit_margin", ascending=False), use_container_width=True)

st.markdown("### 🍔 Product Cluster Analysis")

grouped = filtered_df.groupby("Product").agg({
    "Quantity": "sum",
    "Unit Price": "mean",  # assume fixed menu price
    "Total Product Price": "sum",
    "Cost": "sum"  # from merged cost table
}).reset_index()

grouped["AvgCostPerItem"] = grouped["Cost"] / grouped["Quantity"]
grouped["AvgSalesPrice"] = grouped["Total Product Price"] / grouped["Quantity"]
grouped["ContributionMargin"] = grouped["AvgSalesPrice"] - grouped["AvgCostPerItem"]

# Popularity as % of total
grouped["Popularity"] = grouped["Quantity"] / grouped["Quantity"].sum()

# Set thresholds (can be adjusted)
popularity_threshold = grouped["Popularity"].median()
profitability_threshold = grouped["ContributionMargin"].median()

def classify(row):
    if row["ContributionMargin"] >= profitability_threshold:
        if row["Popularity"] >= popularity_threshold:
            return "Star"
        else:
            return "Puzzle"
    else:
        if row["Popularity"] >= popularity_threshold:
            return "Plowhorse"
        else:
            return "Turtle"

grouped["Category"] = grouped.apply(classify, axis=1)

# 🎯 Quadrant Chart
fig = px.scatter(
    grouped,
    x="ContributionMargin",
    y="Popularity",
    color="Category",
    text="Product",
    hover_data=["Quantity", "Total Product Price", "Cost", "AvgSalesPrice"],
    color_discrete_map={
        "Star": "green",
        "Puzzle": "blue",
        "Plowhorse": "red",
        "Turtle": "gray"
    },
    labels={"ContributionMargin": "Profitability", "Popularity": "Popularity"},
    title="Product Cluster Analysis"
)
fig.update_traces(textposition='top center')
st.plotly_chart(fig, use_container_width=True)

# 📋 KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Number of Menu Items", len(grouped))
col2.metric("Menu Mix % (Top)", f"{(grouped[grouped['Category']=='Star']['Popularity'].sum() * 100):.2f}%")
col3.metric("Average Contribution Margin", f"{grouped['ContributionMargin'].mean():.2f}₺")
col4.metric("Potential Food Cost %", f"{(grouped['AvgCostPerItem'].sum() / grouped['AvgSalesPrice'].sum()) * 100:.2f}%")

