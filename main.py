# main.py
import streamlit as st
import datetime
import sys
from pathlib import Path

# --- Add project root to path for imports ---
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from db.database import init_db, save_entry, get_entry_by_date
from agent.reflection_agent import generate_reflection

# --- Initialize DB ---
init_db()

# --- Page Config ---
st.set_page_config(
    page_title="ConsciousDay Agent",
    page_icon="🌅",
    layout="centered"
)

st.title("🌅 ConsciousDay Journaling Assistant")
st.write("Apna morning journal likho aur AI se reflection + strategy pao.")

# ---------------------------
# Form - User Inputs
# ---------------------------
with st.form("journal_form"):
    st.subheader("📝 Morning Reflection Form")

    journal = st.text_area("✍️ Morning Journal", placeholder="Subha ka experience likho...")
    dream = st.text_area("💭 Dream", placeholder="Koi sapna ya dream share karo...")
    intention = st.text_input("🎯 Intention of the Day", placeholder="Aaj ka main focus kya hai?")
    priorities = st.text_area("✅ Top 3 Priorities", placeholder="1. ... \n2. ... \n3. ...")

    submitted = st.form_submit_button("✨ Generate Reflection")

if submitted:
    # --- Call AI Agent ---
    ai_response = generate_reflection(
        journal=journal,
        intention=intention,
        dream=dream,
        priorities=priorities
    )

    # --- Extract AI outputs ---
    reflection = ai_response.get("reflection", "")
    dream_summary = ai_response.get("dream_summary", "")
    mindset_insight = ai_response.get("mindset", "")
    strategy = ai_response.get("strategy", "")

    # --- Current date ---
    today = datetime.date.today().isoformat()

    # --- Save to DB ---
    save_entry(
        today,
        journal,
        intention,
        dream,
        priorities,
        reflection,
        strategy,
        dream_summary,
        mindset_insight
    )

    st.success("✅ Entry saved to database!")

    st.subheader("🔮 AI Reflection")
    st.markdown(f"""
    **Reflection:** {reflection}  
    **Dream Summary:** {dream_summary}  
    **Mindset Insight:** {mindset_insight}  
    **Day Strategy:** {strategy}  
    """)

# ---------------------------
# Sidebar - Previous Entries
# ---------------------------
st.sidebar.header("📂 Previous Entries")
selected_date = st.sidebar.date_input("Select Date", datetime.date.today())

entries = get_entry_by_date(selected_date.isoformat())

if entries:
    for e in entries:
        st.sidebar.markdown(f"""
        **Date:** {e[1]}  
        **Journal:** {e[2]}  
        **Intention:** {e[3]}  
        **Dream:** {e[4]}  
        **Priorities:** {e[5]}  
        **Reflection:** {e[6]}  
        **Strategy:** {e[7]}  
        **Dream Summary:** {e[8]}  
        **Mindset Insight:** {e[9]}  
        ---
        """)
else:
    st.sidebar.info("No entries found for this date.")
