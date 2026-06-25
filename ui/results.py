from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from calculators.config_loader import get_region_config
from models.results import FeeComparison, FeeResult, ScheduleResult
from services.claude_client import is_claude_available
from services.claude_prompts import advise_on_fee, generate_proposal_narrative


def render_results(
    project,
    fee_result: FeeResult,
    schedule: ScheduleResult,
    comparison: FeeComparison,
) -> None:
    st.subheader("Fee Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Fee", f"${fee_result.total_fee:,.0f}")
    col2.metric("Fee % of Construction", f"{fee_result.fee_as_pct_of_construction:.1f}%")
    col3.metric("Primary Method", fee_result.method.replace("_", " ").title())
    col4.metric(
        "Market Check",
        "In Range" if comparison.market_in_range else "Review",
        delta=f"{comparison.market_min_pct:.0f}–{comparison.market_max_pct:.0f}%",
        delta_color="normal" if comparison.market_in_range else "off",
    )

    st.info(comparison.market_message)

    st.markdown("#### Cross-Method Comparison")
    compare_df = pd.DataFrame(
        [
            {"Method": "Percentage of Construction", "Fee ($)": comparison.percentage_fee},
            {"Method": "Staffing Build-up", "Fee ($)": comparison.staffing_fee},
            {"Method": "Per Drawing Set", "Fee ($)": comparison.drawing_fee},
            {"Method": "Selected Primary", "Fee ($)": comparison.primary_fee},
        ]
    )
    compare_df["Fee ($)"] = compare_df["Fee ($)"].map(lambda value: f"${value:,.0f}")
    st.dataframe(compare_df, width="stretch", hide_index=True)

    if fee_result.notes:
        for note in fee_result.notes:
            st.warning(note)

    st.markdown("#### Phase Fee Breakdown")
    phase_df = pd.DataFrame(
        [
            {
                "Phase": phase.phase_label,
                "Fee %": phase.fee_pct,
                "Fee ($)": phase.fee_amount,
                "Duration (weeks)": phase.duration_weeks,
                "Start": phase.start_date.isoformat(),
                "End": phase.end_date.isoformat(),
            }
            for phase in fee_result.phase_breakdown
        ]
    )
    phase_display = phase_df.copy()
    phase_display["Fee ($)"] = phase_display["Fee ($)"].map(lambda value: f"${value:,.0f}")
    phase_display["Fee %"] = phase_display["Fee %"].map(lambda value: f"{value:.1f}%")
    phase_display["Duration (weeks)"] = phase_display["Duration (weeks)"].map(lambda value: f"{value:.1f}")
    st.dataframe(phase_display, width="stretch", hide_index=True)

    fig = px.bar(
        phase_df,
        x="Phase",
        y="Fee ($)",
        title="Fee by Phase",
        text="Fee ($)",
    )
    fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
    fig.update_layout(yaxis_tickformat="$,.0f", height=400)
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### Schedule Timeline")
    timeline_df = pd.DataFrame(schedule.milestones)
    st.dataframe(timeline_df, width="stretch", hide_index=True)

    gantt_df = pd.DataFrame(
        [
            {
                "Phase": phase.phase_label,
                "Start": phase.start_date,
                "Finish": phase.end_date,
                "Fee ($)": phase.fee_amount,
            }
            for phase in schedule.phases
        ]
    )
    if not gantt_df.empty:
        fig_timeline = px.timeline(
            gantt_df,
            x_start="Start",
            x_end="Finish",
            y="Phase",
            color="Phase",
            title="Project Schedule by Phase",
        )
        fig_timeline.update_yaxes(autorange="reversed")
        fig_timeline.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_timeline, width="stretch")

    csv = timeline_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download schedule (CSV)",
        data=csv,
        file_name=f"{project.name.replace(' ', '_').lower()}_schedule.csv",
        mime="text/csv",
    )

    _render_claude_panel(project, fee_result, comparison)


def _render_claude_panel(project, fee_result: FeeResult, comparison: FeeComparison) -> None:
    st.markdown("---")
    st.subheader("Claude AI Assistant")

    if not is_claude_available():
        st.warning(
            "Claude API is not configured. Set `ANTHROPIC_API_KEY` in a `.env` file "
            "or Streamlit secrets to enable AI features."
        )
        return

    region_label = get_region_config(project.region)["label"]
    project_summary = {
        "name": project.name,
        "type": project.project_type,
        "region": region_label,
        "construction_budget": project.construction_budget,
        "fee_method": project.fee_method,
        "description": project.description,
    }
    fee_payload = {
        "total_fee": fee_result.total_fee,
        "fee_pct": fee_result.fee_as_pct_of_construction,
        "phases": [
            {"phase": p.phase_label, "fee": p.fee_amount, "weeks": p.duration_weeks}
            for p in fee_result.phase_breakdown
        ],
    }
    comparison_payload = comparison.model_dump()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get fee advisory", key="claude_advise"):
            with st.spinner("Claude is reviewing your estimate..."):
                st.session_state.claude_advisory = advise_on_fee(
                    project_summary, fee_payload, comparison_payload
                )
    with col2:
        if st.button("Generate proposal narrative", key="claude_proposal"):
            with st.spinner("Claude is drafting proposal language..."):
                st.session_state.claude_proposal = generate_proposal_narrative(
                    project_summary, fee_payload
                )

    if advisory := st.session_state.get("claude_advisory"):
        st.markdown("#### Fee Advisory")
        st.markdown(advisory)

    if proposal := st.session_state.get("claude_proposal"):
        st.markdown("#### Proposal Narrative")
        st.markdown(proposal)
