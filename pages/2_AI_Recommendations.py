import streamlit as st
from utilities.data_summary import generate_data_summary
from utilities.ai_recommendation import get_structured_recommendations

st.set_page_config(page_title="UseydIntel TR", layout="wide")
st.title("🤖 AI-Powered Recommendations")

data_summary = generate_data_summary()
with st.expander("📄 Summary Used for AI"):
    st.code(data_summary, language="markdown")

ai_response = get_structured_recommendations(data_summary)

st.markdown("#### Recommended Actions")
for block in ai_response.strip().split("\n\n"):
    lines = block.split("\n")
    if len(lines) >= 2:
        action_line = lines[0].strip()
        explanation = lines[1].replace("💡", "").strip()
        col1, col2 = st.columns([0.9, 0.1])
        col1.markdown(f"<div style='word-wrap:break-word; white-space:normal; font-weight:bold;'>{action_line}</div>", unsafe_allow_html=True)
        if col2.button("⚙️", key=action_line):
            st.success("✅ Action triggered.")
        st.markdown(f"💡 _{explanation}_")
        st.markdown("---")
