import streamlit as st
from datetime import datetime
from app import run_multi_agent_workflow, WorkflowInput

st.set_page_config(page_title="Research System", page_icon="📊", layout="centered")

# ---------------------------
# Session State for History
# ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []

st.title("📊 Multi-Agent Research System")
st.write("Research assistant using Web + Wikipedia + ArXiv sources")

# ---------------------------
# Sidebar – Research History (Non-AI)
# ---------------------------
st.sidebar.title("🕒 Research History")

if st.session_state.history:
    for i, item in enumerate(reversed(st.session_state.history), 1):
        st.sidebar.write(f"{i}. {item}")
else:
    st.sidebar.write("No history yet.")

st.sidebar.write("---")
if st.sidebar.button("🧹 Clear History"):
    st.session_state.history = []

# ---------------------------
# Main Section: Research Tool
# ---------------------------
st.header("🔎 Research Assistant")

query = st.text_input("Research Topic:", placeholder="e.g., Latest AI trends in India")
start = st.button("🚀 Start Research")

result = None
generated_time = None

if start:
    if not query.strip():
        st.warning("Please enter a topic before starting.")
    else:
        with st.spinner("Agents are researching... Please wait."):
            result = run_multi_agent_workflow(WorkflowInput(query=query))
            generated_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

        # Save to history
        st.session_state.history.append(query)

        st.write("---")

        tab1, tab2, tab3 = st.tabs(["🔎 Research Data", "📑 Summary", "✉ Email"])

        # ---------------- Research Tab ----------------
        with tab1:
            st.subheader("Raw Research Data")
            st.text(result["raw_research"])

        # ---------------- Summary Tab ----------------
        with tab2:
            summary = result["raw_summary"]

            st.subheader("Executive Summary")
            st.write(summary.get("executive_summary", "No summary found."))

            st.subheader("Action Items")
            action_items = summary.get("action_items", [])
            if action_items:
                for item in action_items:
                    st.write(f"- {item}")
            else:
                st.write("No action items detected.")

            # Copy Summary button
            st.download_button(
                label="📋 Copy Summary (TXT)",
                data=summary.get("executive_summary", ""),
                file_name="summary.txt",
                mime="text/plain"
            )

        # ---------------- Email Tab ----------------
        with tab3:
            st.subheader("Generated Email")
            st.text_area("", result["final_email"], height=250)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="⬇ Download Email",
                    data=result["final_email"],
                    file_name="generated_email.txt",
                    mime="text/plain"
                )

            with col2:
                st.download_button(
                    label="📋 Copy Email",
                    data=result["final_email"],
                    file_name="email_copy.txt",
                    mime="text/plain"
                )

        # ---------------- Full Report Download ----------------
        full_report = f"""
Research Topic: {query}
Generated on: {generated_time}

====================
RAW RESEARCH
====================
{result['raw_research']}

====================
SUMMARY
====================
{summary.get('executive_summary', '')}

Action Items:
"""

        for item in summary.get("action_items", []):
            full_report += f"- {item}\n"

        full_report += f"""

====================
EMAIL
====================
{result['final_email']}
"""

        st.write("---")
        st.download_button(
            label="📄 Download Full Report",
            data=full_report,
            file_name="research_report.txt",
            mime="text/plain"
        )

        # ---------------- Timestamp ----------------
        st.info(f"Report generated on: {generated_time}")

# ---------------------------
# Footer
# ---------------------------
st.write("---")
st.caption("Developed by Abhishek Shrotriya | Infosys Springboard Internship – Batch 8 | Mentor: Simran Ma’am | Coordinator: Heema Ma’am")
