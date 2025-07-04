from openai import OpenAI
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
api_key =  os.getenv("openai_key") or st.secrets.get("openai_key")

client = OpenAI(api_key=api_key)

def get_structured_recommendations(data_summary):
    prompt = f"""
You are a restaurant business strategist helping an owner act on performance insights.

Your task is to generate **3 clear and actionable recommendations**, using sales trends, item performance, and inventory data.

Each recommendation must follow this exact format:

---

Action: [Natural sentence describing the recommendation. Example: "Apply a 15% discount on Tavuk Şiş this Saturday."]
Action Type: [discount] or [bundle promotion] or [availability update]
Date Range: [e.g., "Saturday, July 6" or "July 10–15"]
Explanation: [Start with "💡" and give a clear, data-driven reason why this helps.]

---

📌 Notes:
- Do not group items.
- Each action must target only one item (or one combo).
- Use realistic restaurant language.
- Use actual weekday or date ranges.
- Always include the Explanation section for every recommendation.

Here is the data to work from:

\"\"\"
{data_summary}
\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a structured restaurant strategy advisor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=600  # increase to avoid trimming
    )
    return response.choices[0].message.content.strip()