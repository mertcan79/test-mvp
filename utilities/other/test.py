import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import openai
import os
from dotenv import load_dotenv

# ------------------------
# Setup
# ------------------------
load_dotenv()
openai.api_key = os.getenv("openai_key")

st.set_page_config(page_title="UseydIntel TR", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f9f9fb;}
        .stDataFrame th {background-color: #f1f3f6; color: #333;}
    </style>
""", unsafe_allow_html=True)

# ------------------------
# Sidebar Filters
# ------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3595/3595455.png", width=80)
st.sidebar.title("📍 Market Filters")
selected_district = st.sidebar.selectbox("District", ["Kadıköy", "Beşiktaş", "Şişli"])
selected_category = st.sidebar.selectbox("Category", ["Burger", "Pizza", "Kebap", "Vegan", "Dessert"])

# ------------------------
# Load Real Data
# ------------------------
@st.cache_data
def load_real_data():
    try:
        return pd.read_csv("data.csv")  # Replace with dynamic path if needed
    except FileNotFoundError:
        st.error("Real data file not found. Please ensure 'data.csv' exists.")
        return pd.DataFrame()

data = load_real_data()
filtered = data[(data['District'] == selected_district) & (data['Category'] == selected_category)]

st.title("📊 UseydIntel TR – Restaurant Competitive Intelligence")
st.markdown("Gain strategic insights from your food delivery market in real-time. 🧠")

col1, col2 = st.columns([3, 2])
with col1:
    st.subheader(f"📌 Competitor Overview: {selected_district} / {selected_category}")
    st.dataframe(filtered, use_container_width=True, height=400)

with col2:
    st.metric("Avg Discount (%)", f"{filtered['Discount (%)'].mean():.1f}%")
    st.metric("Avg Item Price (₺)", f"{filtered['Avg Item Price (₺)'].mean():.2f}₺")
    st.metric("Avg ROI Potential (%)", f"{filtered['Est. ROI Increase (%)'].mean():.1f}%")

# ------------------------
# Plot: Discount vs Price
# ------------------------
st.subheader("📉 Discount vs. Price vs. ROI")
fig = px.scatter(
    filtered,
    x="Avg Item Price (₺)",
    y="Discount (%)",
    color="Est. ROI Increase (%)",
    hover_data=["Restaurant", "Promo Type", "Top Item"],
    title="🎯 Optimal Pricing and Discount Strategy",
    color_continuous_scale='Turbo',
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# ------------------------
# AI-Powered Insight
# ------------------------
st.subheader("🤖 AI-Powered Insight")

@st.cache_data(show_spinner=False)
def get_ai_analysis(df):
    prompt = f"""
    Analyze this restaurant competition data in the {selected_district} district under the {selected_category} category. Provide strategic insights, trends, and suggestions based on the following data:

    {df.to_string(index=False)}

    Please format the output in bullet points.
    """ 
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful marketing & business analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

if not filtered.empty:
    with st.spinner("Analyzing market with GPT-4..."):
        insights = get_ai_analysis(filtered)
        st.markdown(insights)
else:
    st.warning("No data available for the selected filters.")
