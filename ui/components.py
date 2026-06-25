from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from calculators.config_loader import (
    get_drawing_disciplines,
    get_phases,
    get_project_type_config,
    get_region_config,
    load_market_rates,
)
from calculators.staffing_fee import default_staff_for_project
from models.project import DrawingDiscipline, DrawingSet, Project, StaffMember


def _project_type_options() -> dict[str, str]:
    types = load_market_rates()["project_types"]
    return {key: value["label"] for key, value in types.items()}


def _region_options() -> dict[str, str]:
    regions = load_market_rates()["regions"]
    return {key: value["label"] for key, value in regions.items()}


def render_sidebar() -> dict:
    st.sidebar.header("Project Setup")
    type_options = _project_type_options()
    region_options = _region_options()

    project_type = st.sidebar.selectbox(
        "Project type",
        options=list(type_options.keys()),
        format_func=lambda key: type_options[key],
        key="project_type",
    )
    region = st.sidebar.selectbox(
        "Market region",
        options=list(region_options.keys()),
        format_func=lambda key: region_options[key],
        key="region",
    )

    type_config = get_project_type_config(project_type)
    st.sidebar.caption(
        f"Market fee range: {type_config['fee_pct_min']:.0f}%–"
        f"{type_config['fee_pct_max']:.0f}% of construction"
    )

    project_name = st.sidebar.text_input("Project name", value="Sample Project", key="project_name")
    construction_budget = st.sidebar.number_input(
        "Construction budget ($)",
        min_value=10_000,
        value=1_000_000,
        step=50_000,
        key="construction_budget",
    )
    fee_method = st.sidebar.selectbox(
        "Primary fee method",
        options=["percentage", "staffing", "per_drawing", "stipulated_sum"],
        format_func=lambda x: {
            "percentage": "% of Construction Cost",
            "staffing": "Staffing Build-up",
            "per_drawing": "Per Drawing Set",
            "stipulated_sum": "Stipulated Sum",
        }[x],
        key="fee_method",
    )

    fee_percentage = type_config["fee_pct_default"]
    stipulated_sum = None
    if fee_method == "percentage":
        fee_percentage = st.sidebar.slider(
            "Fee percentage",
            min_value=float(type_config["fee_pct_min"]),
            max_value=float(type_config["fee_pct_max"]),
            value=float(type_config["fee_pct_default"]),
            step=0.5,
            key="fee_percentage",
        )
    elif fee_method == "stipulated_sum":
        default_sum = construction_budget * (type_config["fee_pct_default"] / 100.0)
        stipulated_sum = st.sidebar.number_input(
            "Stipulated sum ($)",
            min_value=1_000.0,
            value=float(default_sum),
            step=5_000.0,
            key="stipulated_sum",
        )
        fee_percentage = (stipulated_sum / construction_budget) * 100.0
    else:
        fee_percentage = st.sidebar.number_input(
            "Reference fee % (for comparison)",
            min_value=1.0,
            max_value=30.0,
            value=float(type_config["fee_pct_default"]),
            step=0.5,
            key="fee_percentage_ref",
        )

    start_date = st.sidebar.date_input("Project start date", value=date.today(), key="start_date")
    total_weeks = st.sidebar.number_input(
        "Total duration (weeks)",
        min_value=8,
        value=int(type_config["default_weeks"]),
        step=1,
        key="total_weeks",
    )
    include_bidding = st.sidebar.checkbox("Include bidding phase", value=True, key="include_bidding")
    include_ca = st.sidebar.checkbox("Include construction admin (CA)", value=True, key="include_ca")

    description = st.sidebar.text_area(
        "Project description (optional, for Claude)",
        height=100,
        placeholder="e.g. 4,500 SF custom home, coastal CA, full services with CA...",
        key="description",
    )

    return {
        "project_name": project_name,
        "project_type": project_type,
        "region": region,
        "construction_budget": construction_budget,
        "fee_method": fee_method,
        "fee_percentage": fee_percentage,
        "stipulated_sum": stipulated_sum,
        "start_date": start_date,
        "total_weeks": total_weeks,
        "include_bidding": include_bidding,
        "include_ca": include_ca,
        "description": description,
    }


def _ensure_staff_defaults() -> None:
    if "staff_df" not in st.session_state:
        staff = default_staff_for_project(
            st.session_state.get("project_type", "custom_residential"),
            st.session_state.get("region", "medium"),
            int(st.session_state.get("total_weeks", 40)),
        )
        st.session_state.staff_df = pd.DataFrame(
            [
                {
                    "Role": member.role_label,
                    "role_key": member.role_key,
                    "Hourly Rate ($)": member.hourly_rate,
                    "SD Hours": member.hours_sd,
                    "DD Hours": member.hours_dd,
                    "CD Hours": member.hours_cd,
                    "Bidding Hours": member.hours_bidding,
                    "CA Hours": member.hours_ca,
                }
                for member in staff
            ]
        )


def render_staff_tab() -> list[StaffMember]:
    st.subheader("Staff Resources & Fee Structure")
    st.caption("Edit hourly rates and estimated hours per AIA phase. Used for the staffing build-up cross-check.")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Reset to defaults"):
            if "staff_df" in st.session_state:
                del st.session_state.staff_df
            st.rerun()

    _ensure_staff_defaults()
    edited = st.data_editor(
        st.session_state.staff_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "role_key": None,
            "Hourly Rate ($)": st.column_config.NumberColumn(min_value=1, format="$%.2f"),
            "SD Hours": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            "DD Hours": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            "CD Hours": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            "Bidding Hours": st.column_config.NumberColumn(min_value=0, format="%.0f"),
            "CA Hours": st.column_config.NumberColumn(min_value=0, format="%.0f"),
        },
        hide_index=True,
        key="staff_editor",
    )
    st.session_state.staff_df = edited

    staff: list[StaffMember] = []
    for _, row in edited.iterrows():
        if not row.get("Role"):
            continue
        staff.append(
            StaffMember(
                role_key=str(row.get("role_key") or row["Role"].lower().replace(" ", "_")),
                role_label=str(row["Role"]),
                hourly_rate=float(row["Hourly Rate ($)"]),
                hours_sd=float(row["SD Hours"]),
                hours_dd=float(row["DD Hours"]),
                hours_cd=float(row["CD Hours"]),
                hours_bidding=float(row["Bidding Hours"]),
                hours_ca=float(row["CA Hours"]),
            )
        )
    return staff


def render_milestones_tab(sidebar: dict) -> tuple[dict[str, float], dict[str, float]]:
    st.subheader("Milestones & Phase Allocation")
    st.caption("Adjust fee and duration splits across AIA basic service phases. Percentages auto-normalize.")

    phases = get_phases()
    active_keys = []
    for key in phases:
        if key == "bidding" and not sidebar["include_bidding"]:
            continue
        if key == "construction_admin" and not sidebar["include_ca"]:
            continue
        active_keys.append(key)

    fee_cols = st.columns(len(active_keys))
    fee_pcts: dict[str, float] = {}
    for col, key in zip(fee_cols, active_keys):
        with col:
            fee_pcts[key] = st.number_input(
                f"{phases[key]['label']} — Fee %",
                min_value=0.0,
                max_value=100.0,
                value=float(phases[key]["fee_pct"]),
                step=1.0,
                key=f"fee_pct_{key}",
            )

    duration_cols = st.columns(len(active_keys))
    duration_pcts: dict[str, float] = {}
    for col, key in zip(duration_cols, active_keys):
        with col:
            duration_pcts[key] = st.number_input(
                f"{phases[key]['label']} — Duration %",
                min_value=0.0,
                max_value=100.0,
                value=float(phases[key]["duration_pct"]),
                step=1.0,
                key=f"dur_pct_{key}",
            )

    fee_total = sum(fee_pcts.values())
    dur_total = sum(duration_pcts.values())
    if abs(fee_total - 100) > 0.01:
        st.warning(f"Fee phase percentages sum to {fee_total:.0f}% (will be normalized to 100%).")
    if abs(dur_total - 100) > 0.01:
        st.warning(f"Duration percentages sum to {dur_total:.0f}% (will be normalized to 100%).")

    return fee_pcts, duration_pcts


def render_drawings_tab(sidebar: dict) -> DrawingSet:
    st.subheader("Drawing Set")
    st.caption("Sheet counts drive the per-drawing fee cross-check.")

    type_config = get_project_type_config(sidebar["project_type"])
    complexity = st.selectbox(
        "Drawing complexity",
        options=["simple", "standard", "complex"],
        index=1,
        key="drawing_complexity",
    )
    revision_rounds = st.number_input(
        "Revision rounds included",
        min_value=0,
        max_value=6,
        value=2,
        key="revision_rounds",
    )

    disciplines_config = get_drawing_disciplines()
    if "drawing_df" not in st.session_state:
        default_sheets = int(type_config["default_arch_sheets"])
        st.session_state.drawing_df = pd.DataFrame(
            [
                {"Discipline": cfg["label"], "discipline_key": key, "Sheets": default_sheets if key == "architectural" else 0}
                for key, cfg in disciplines_config.items()
            ]
        )

    edited = st.data_editor(
        st.session_state.drawing_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "discipline_key": None,
            "Sheets": st.column_config.NumberColumn(min_value=0, step=1),
        },
        hide_index=True,
        key="drawing_editor",
    )
    st.session_state.drawing_df = edited

    disciplines: list[DrawingDiscipline] = []
    for _, row in edited.iterrows():
        if int(row["Sheets"]) <= 0:
            continue
        disciplines.append(
            DrawingDiscipline(
                discipline_key=str(row.get("discipline_key") or "architectural"),
                discipline_label=str(row["Discipline"]),
                sheet_count=int(row["Sheets"]),
            )
        )

    return DrawingSet(
        disciplines=disciplines,
        complexity=complexity,
        revision_rounds=int(revision_rounds),
    )


def build_project(
    sidebar: dict,
    staff: list[StaffMember],
    fee_pcts: dict[str, float],
    duration_pcts: dict[str, float],
    drawing_set: DrawingSet,
) -> Project:
    return Project(
        name=sidebar["project_name"],
        project_type=sidebar["project_type"],
        region=sidebar["region"],
        construction_budget=sidebar["construction_budget"],
        fee_percentage=sidebar["fee_percentage"],
        fee_method=sidebar["fee_method"],
        stipulated_sum=sidebar.get("stipulated_sum"),
        start_date=sidebar["start_date"],
        total_weeks=int(sidebar["total_weeks"]),
        include_ca=sidebar["include_ca"],
        include_bidding=sidebar["include_bidding"],
        phase_fee_pcts=fee_pcts,
        phase_duration_pcts=duration_pcts,
        staff=staff,
        drawing_set=drawing_set,
        description=sidebar.get("description", ""),
    )
