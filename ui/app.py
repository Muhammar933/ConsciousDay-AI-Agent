import streamlit as st
import datetime
import sys
from pathlib import Path

# --- Path Setup for DB & Agent ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from db.database import init_db, save_entry, get_entry_by_date
from agent.reflection_agent import get_ai_reflection  # Agent function import

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
    today = datetime.date.today().isoformat()

    # --- Call AI Agent ---
    try:
        ai_response = get_ai_reflection(
            journal=journal,
            dream=dream,
            intention=intention,
            priorities=priorities
        )

        reflection = ai_response.get("reflection", "")
        dream_summary = ai_response.get("dream_summary", "")
        mindset_insight = ai_response.get("mindset_insight", "")
        strategy = ai_response.get("strategy", "")

        # --- Save to DB ---
        save_entry(
            date=today,
            journal=journal,
            intention=intention,
            dream=dream,
            priorities=priorities,
            reflection=reflection,
            strategy=strategy,
            dream_summary=dream_summary,
            mindset_insight=mindset_insight
        )

        st.success("✅ Entry saved to database!")

        st.subheader("🔮 AI Reflection")
        st.markdown(f"""
        **Reflection:** {reflection}  
        **Dream Summary:** {dream_summary}  
        **Mindset Insight:** {mindset_insight}  
        **Day Strategy:** {strategy}  
        """)

    except Exception as e:
        st.error(f"❌ AI agent call failed: {e}")

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
        **Dream Summary:** {e[8]}  
        **Mindset Insight:** {e[9]}  
        **Strategy:** {e[7]}  
        ---
        """)
else:
    st.sidebar.info("No entries found for this date.")
