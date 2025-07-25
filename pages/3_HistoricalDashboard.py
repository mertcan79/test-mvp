# dashboard_v2.py
import os
import re
import json
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
import numpy as np

# --------------------  CONFIG & STYLES  -------------------- #
st.set_page_config(page_title="2025 Sales Dashboard", layout="wide")
if os.path.exists("logo.png"):  # optional
    st.image(Image.open("logo.png"), width=150)

# keep previous colour palette / fonts (borrowed from v1) 
st.markdown(
    """
    <style>
      .main, .css-18e3th9 {background:#f7f8ff;}
      .stApp {color:#333;}
      .primary {color:#2E2EFF;}
      .css-1d391kg {background-color:#2E2EFF!important;}
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = "data/historical"

# ---------------  HELPERS  ---------------- #
def to_snake(c):
    c = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", c)
    return c.replace(" ", "_").lower()

@st.cache_data(show_spinner=False)
def load_all():
    orders = pd.read_csv(os.path.join(DATA_DIR, "completed_orders_2025.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "products_2025.csv"))
    payments = pd.read_csv(os.path.join(DATA_DIR, "payments_2025.csv"))
    features = pd.read_csv(os.path.join(DATA_DIR, "features_2025.csv"))

    # harmonise column names
    orders.columns = [to_snake(c) for c in orders.columns]
    products.columns = [to_snake(c) for c in products.columns]
    payments.columns = [to_snake(c) for c in payments.columns]
    features.columns = [to_snake(c) for c in features.columns]

    # key fixes / parses
    orders = orders.rename(columns={"id": "order_id"})
    orders["insert_date"] = pd.to_datetime(orders["insert_date"], errors="coerce")
    orders["delivery_time"] = pd.to_datetime(orders["delivery_time"], errors="coerce")
    orders["hour"] = orders["insert_date"].dt.hour
    orders["time_of_day"] = pd.cut(
        orders["hour"],
        bins=[-1, 5, 10, 15, 21, 24],
        labels=["Night-Owl", "Breakfast", "Lunch", "Dinner", "Late-Night"],
    )

    # derive simple district from customer_region
    def extract_dist(x):
        if pd.isna(x):
            return None
        x = str(x).lower()
        for d in [
            "adalar","arnavutköy","ataşehir","avcılar","bağcılar","bahçelievler",
            "bakırköy","başakşehir","bayrampaşa","beşiktaş","beykoz","beylikdüzü",
            "beyoğlu","büyükçekmece","çatalca","çekmeköy","esenler","esenyurt",
            "eyüpsultan","fatih","gaziosmanpaşa","güngören","kadıköy","kağıthane",
            "kartal","küçükçekmece","maltepe","pendik","sancaktepe","sar yer",
            "silivri","sultanbeyli","sultangazi","şile","şişli","tuzla","üsküdar",
            "ümraniye","zeytinburnu",
        ]:
            if d.replace(" "," ").strip() in x:
                return d.title()
        return "Diğer"
    orders["district"] = orders["customer_region"].apply(extract_dist)

    # enrich orders with product & feature facts
    prod_sum = (products.groupby("order_id")
                .agg(product_count=("quantity","sum"),
                     item_total=("total_amount","sum"))
                .reset_index())
    orders = orders.merge(prod_sum, how="left", on="order_id")

    feat_sum = (features.merge(products[["order_product_id","order_id"]],
                               on="order_product_id")
                .groupby("order_id")
                .agg(feature_extra=("additional_price","sum"))
                .reset_index())
    orders = orders.merge(feat_sum, how="left", on="order_id")

    pay_sum = (payments.groupby("order_id")
               .agg(paid_amount=("amount","sum"),
                    payment_methods=("payment_name", lambda x: ", ".join(sorted(set(x)))))
               .reset_index())
    orders = orders.merge(pay_sum, how="left", on="order_id")

    # default zeros
    orders[["feature_extra","product_count"]] = orders[["feature_extra","product_count"]].fillna(0)

    return orders, products, payments, features

orders, products, payments, features = load_all()

# ---------------  SIDEBAR FILTERS  ---------------- #
st.sidebar.header("Filters")
min_d, max_d = orders["insert_date"].min().date(), orders["insert_date"].max().date()
date_range = st.sidebar.date_input("Tarih aralığı", [min_d, max_d])
apps   = st.sidebar.multiselect("Uygulama", sorted(orders["external_app_name"].dropna().unique()))
payms  = st.sidebar.multiselect("Ödeme Tipi", sorted(payments["payment_name"].dropna().unique()))
dists  = st.sidebar.multiselect("İlçe", sorted(orders["district"].dropna().unique()))

mask = orders["insert_date"].dt.date.between(*date_range)
if apps:  mask &= orders["external_app_name"].isin(apps)
if dists: mask &= orders["district"].isin(dists)
if payms:
    pay_orders = payments[payments["payment_name"].isin(payms)]["order_id"].unique()
    mask &= orders["order_id"].isin(pay_orders)

view = orders[mask]

# ----------------  KPI SECTION  -------------- #
st.title("📊 2025 Sales Dashboard")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Ciro (₺)", f"{view['order_total'].sum():,.2f}")
k2.metric("Sipariş", view["order_id"].nunique())
k3.metric("Sepet Ort.", f"{view['order_total'].mean():,.2f}")
k4.metric("Ürün / Sipariş", f"{view['product_count'].mean():.2f}")
k5.metric("Ekstra Özellik Geliri (₺)", f"{view['feature_extra'].sum():,.2f}")

st.markdown("---")

# -------------  CHARTS  ---------------- #
c1, c2 = st.columns(2)
with c1:
    fig = px.pie(view, values="order_total", names="external_app_name",
                 title="Ciro | Platform")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    pay_merged = payments.merge(view[["order_id"]], on="order_id")
    fig = px.pie(pay_merged, values="amount", names="payment_name",
                 title="Ciro | Ödeme Metodu")
    st.plotly_chart(fig, use_container_width=True)

# Category chart
cat_sales = (products.merge(view[["order_id"]], on="order_id")
                     .groupby("category")["total_amount"]
                     .sum().sort_values())
st.subheader("🍔 Satış | Kategori")
st.bar_chart(cat_sales, use_container_width=True)

# Time-series
ts = (view.groupby(view["insert_date"].dt.date)["order_total"]
           .sum().rename_axis("date").reset_index())
st.subheader("📈 Günlük Ciro")
st.line_chart(ts, x="date", y="order_total", use_container_width=True)

# District heat-map (optional Mapbox token not required)
try:
    geo = requests.get(
        "https://raw.githubusercontent.com/ozanyerli/istanbul-districts-geojson/main/istanbul-districts.json"
    ).json()
    dist_sales = view.groupby("district")["order_total"].sum().reset_index()
    dist_sales["dist_norm"] = dist_sales["district"].str.lower().str.replace("ı","i")
    for f in geo["features"]:
        f["properties"]["dist_norm"] = f["properties"]["name"].lower().replace("ı","i")
    fig = px.choropleth_mapbox(
        dist_sales, geojson=geo, locations="dist_norm",
        featureidkey="properties.dist_norm", color="order_total",
        color_continuous_scale="Reds", mapbox_style="carto-positron",
        zoom=9, center={"lat":41.05,"lon":28.98},
        title="İlçe Bazlı Ciro"
    )
    fig.update_layout(margin={"r":0,"l":0,"t":40,"b":0})
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.info("Harita yüklenemedi → "+str(e))

# -------------  RAW TABLES (all columns preserved) ------------- #
with st.expander("📄 Tüm Verileri Gör"):
    tabs = st.tabs(["Orders","Products","Payments","Features"])
    tabs[0].dataframe(view, use_container_width=True)
    tabs[1].dataframe(products, use_container_width=True)
    tabs[2].dataframe(payments, use_container_width=True)
    tabs[3].dataframe(features, use_container_width=True)

st.subheader("✨ Product Cluster — Popularity vs Profitability")

# crude cost proxy (delete if you have true cost column)
products["estimated_cost"] = products.get("unitprice", 0) * 0.8

perf = (
    products.groupby("product_name")  # <-- corrected column name
    .agg(
        popularity=("quantity", "sum"),
        total_revenue=("total_amount", "sum"),  # <-- use total_amount, not item_total
        total_cost=("estimated_cost", "sum"),
    )
    .reset_index()
)

# avoid divide‑by‑zero and keep only products that sold at least once
perf = perf[perf["popularity"] > 0]

# per‑item profitability & bubble size
perf["profitability"] = (perf["total_revenue"] - perf["total_cost"]) / perf["popularity"]
perf["bubble"] = np.maximum(perf["total_revenue"] - perf["total_cost"], 1)

fig = px.scatter(
    perf,
    x="profitability",
    y="popularity",
    size="bubble",
    hover_name="product_name",
    color="product_name",
    labels=dict(profitability="₺ Profit / Item", popularity="Qty Sold"),
    title="Product Cluster Analysis",
)

st.plotly_chart(fig, use_container_width=True)


# ╭───────────────────────── 2) CUSTOMER COHORT ───────────────────╮
# Heat-map : months since first purchase  ×  cohort month
# ---------------------------------------------------------------
st.subheader("👥 Customer Cohort Analysis")

ord_copy = orders.copy()
ord_copy["order_month"]  = ord_copy["insert_date"].dt.to_period("M")
ord_copy["cohort_month"] = (
    ord_copy.groupby("customer_id")["insert_date"]
            .transform("min").dt.to_period("M")
)

cohort = (
    ord_copy.groupby(["cohort_month", "order_month"])["customer_id"]
            .nunique()
            .reset_index(name="n_customers")
)
cohort["cohort_index"] = (
    cohort["order_month"] - cohort["cohort_month"]
).apply(lambda x: x.n)

pivot = (
    cohort.pivot(index="cohort_month",
                 columns="cohort_index",
                 values="n_customers")
          .sort_index(ascending=False)
)

# 👉 make both axes JSON-serialisable
pivot.index   = pivot.index.astype(str)   # e.g. “2025-06”
pivot.columns = pivot.columns.astype(str) # 0,1,2,…

fig = px.imshow(
    pivot,
    text_auto=True,
    aspect="auto",
    color_continuous_scale="YlOrBr",
    labels=dict(x="Months Since First Order",
                y="Cohort (Join Month)",
                color="Customers"),
    title="Customer Cohort Analysis",
)
st.plotly_chart(fig, use_container_width=True)


# ╭───────────────────────── 3) WEEKDAY DISTRIBUTION ──────────────╮
# External App Name × Weekday  (% share of that app's total sales)
# ---------------------------------------------------------------
st.subheader("📆 Weekday Sales Mix by Delivery Platform")

# ─── Weekday Sales Mix by Delivery Platform (patch) ──────────────
wk_orders = orders.copy()
wk_orders["weekday"] = wk_orders["insert_date"].dt.day_name()
weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
wk_orders["weekday"] = pd.Categorical(wk_orders["weekday"],
                                      categories=weekday_order, ordered=True)

wd = (
    wk_orders.groupby(["external_app_name", "weekday"])["order_total"]
             .sum()
             .reset_index()
)

# ✅ index-aligned; no more TypeError
total_per_app = wd.groupby("external_app_name")["order_total"].transform("sum")
wd["pct_of_app"] = wd["order_total"] / total_per_app * 100

heat = (
    wd.pivot(index="external_app_name",
             columns="weekday",
             values="pct_of_app")
      .fillna(0)[weekday_order]        # keep column order
)

fig = px.imshow(
    heat,
    text_auto=".1f",
    aspect="auto",
    color_continuous_scale="RdYlBu",
    labels=dict(x="Weekday", y="Platform", color="% of Weekly GMV"),
    title="Delivery-App Weekday Contribution (%)"
)
fig.update_xaxes(side="top")
st.plotly_chart(fig, use_container_width=True)