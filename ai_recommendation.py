from openai import OpenAI
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
api_key = st.secrets.get("openai_key") or os.getenv("openai_key")

client = OpenAI(api_key=api_key)

def get_structured_recommendations(data_summary):
    prompt = f"""
You are a restaurant strategy assistant.

Your job is to generate **3 concise, actionable recommendations** in the exact format below. Do not use vague terms. Use one item per recommendation.

⚠️ OUTPUT FORMAT:
[Item] [Action] [Action Detail] [Date Range]  
💡 Explanation: [Why this helps — reference trends, revenue, or day-based patterns.]

📌 Only use these action types: [discount], [bundle promotion], [menu highlight], [availability update].

📌 Action details must include numbers or specifics (e.g., “15% discount”, “bundle with Ayran”, “highlight on homepage”).

📌 Date range must use **realistic formats**: “Saturday, July 6” or “July 8–10”.

📌 Do not group items. One recommendation per item.

EXAMPLES:
Tavuk İskender → Apply 15% discount [discount] [Saturday, July 6]  
💡 Explanation: Sales dropped 3 days in a row. Saturday is the slowest day; a discount could boost orders.

Ayran → Bundle with Tavuk Wrap [bundle promotion] [Weekdays: July 8–12]  
💡 Explanation: Ayran underperforms solo. Pairing it with a best-seller can increase average ticket value.

Cheesecake → Highlight in dessert section [menu highlight] [July 10–20]  
💡 Explanation: Cheesecake peaked last Friday. Menu highlight could ride the wave.

🔽
Use the following data to generate recommendations:
\"\"\" 
{data_summary}
\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a structured restaurant optimization assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()