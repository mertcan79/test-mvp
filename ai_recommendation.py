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

Your task: Generate **3 clear and professional recommendations** using item-level trends, ordering patterns, and menu performance.

Each recommendation must have:

**1. A natural language action line**, like:
- “Apply a 15% discount on Tavuk İskender this Saturday”
- “Bundle Ayran with Tavuk Wrap from July 8–12”
- “Highlight Cheesecake on the menu between July 10–20”

**2. A short explanation below it**, starting with:
💡 Explanation: [Reason — data-driven, clear, tactical]

📌 Allowed action types: [discount], [bundle promotion], [availability update]  
📌 Action line must include:  
- Item name  
- What you want the restaurant to do  
- Specific details (e.g., 10% discount, bundle with X)  
- Time range using **natural phrasing** (e.g. “next weekend”, “July 5–10”, “this Friday”)

📌 Each recommendation must be for only one item (or one bundle). No grouping.

---

EXAMPLES:

Apply a 15% discount on Tavuk İskender this Saturday [discount] [Saturday, July 6]  
💡 Explanation: Sales dropped 3 days in a row. Saturday is the slowest day; a discount could boost orders.

Bundle Ayran with Tavuk Wrap for weekday lunch hours [bundle promotion] [July 8–12]  
💡 Explanation: Ayran underperforms solo. Pairing it with a best-seller increases basket size.

---

Now generate your recommendations based on the following data:

\"\"\"
{data_summary}
\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a data-driven and articulate restaurant business assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=450
    )
    return response.choices[0].message.content.strip()