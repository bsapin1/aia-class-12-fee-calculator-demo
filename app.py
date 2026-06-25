"""Architectural fee calculator — Streamlit prototype."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from calculators.engine import run_calculations
from services.claude_client import is_claude_available
from services.claude_prompts import analyze_project_description
from ui.components import (
    build_project,
    render_drawings_tab,
    render_milestones_tab,
    render_sidebar,
    render_staff_tab,
)
from ui.results import render_results

load_dotenv()

st.set_page_config(
    page_title="Architectural Fee Calculator",
    page_icon="🏛️",
    layout="wide",
)

st.title("🏛️ Architectural Fee Calculator")
st.caption(
    "Indicative fee estimates for architectural professionals. "
    "Educational prototype — not legal or contractual advice."
)

if is_claude_available():
    st.sidebar.success("Claude API connected")
else:
    st.sidebar.info("Claude API not configured (optional)")

sidebar = render_sidebar()

if sidebar.get("description") and is_claude_available():
    if st.sidebar.button("Analyze project with Claude"):
        with st.spinner("Analyzing project description..."):
            try:
                analysis = analyze_project_description(sidebar["description"])
                st.session_state.project_type = analysis.get("project_type", sidebar["project_type"])
                st.session_state.region = analysis.get("region", sidebar["region"])
                st.session_state.construction_budget = int(analysis.get("construction_budget", sidebar["construction_budget"]))
                st.session_state.fee_percentage = float(analysis.get("fee_percentage", sidebar["fee_percentage"]))
                st.session_state.total_weeks = int(analysis.get("total_weeks", sidebar["total_weeks"]))
                st.session_state.include_ca = bool(analysis.get("include_ca", True))
                st.session_state.include_bidding = bool(analysis.get("include_bidding", True))
                st.session_state.drawing_complexity = analysis.get("complexity", "standard")
                st.session_state.claude_analysis = analysis
                if "drawing_df" in st.session_state and analysis.get("estimated_arch_sheets"):
                    st.session_state.drawing_df.loc[
                        st.session_state.drawing_df["discipline_key"] == "architectural",
                        "Sheets",
                    ] = int(analysis["estimated_arch_sheets"])
                if "staff_df" in st.session_state:
                    del st.session_state.staff_df
                st.rerun()
            except Exception as exc:
                st.sidebar.error(f"Claude analysis failed: {exc}")

if analysis := st.session_state.get("claude_analysis"):
    with st.expander("Claude project analysis", expanded=False):
        st.write(analysis.get("rationale", ""))
        if risks := analysis.get("risks"):
            st.markdown("**Risks:**")
            for risk in risks:
                st.markdown(f"- {risk}")

tab_staff, tab_milestones, tab_drawings, tab_results = st.tabs(
    ["Staff & Rates", "Milestones", "Drawing Set", "Results"]
)

with tab_staff:
    staff = render_staff_tab()

with tab_milestones:
    fee_pcts, duration_pcts = render_milestones_tab(sidebar)

with tab_drawings:
    drawing_set = render_drawings_tab(sidebar)

project = build_project(sidebar, staff, fee_pcts, duration_pcts, drawing_set)

try:
    fee_result, schedule, comparison = run_calculations(project)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

with tab_results:
    render_results(project, fee_result, schedule, comparison)

st.markdown("---")
st.caption(
    "Market benchmarks sourced from industry references (AIA B101 phase structure, "
    "Archtoolbox, Monograph, regional surveys). Verify all figures for your jurisdiction and project."
)
