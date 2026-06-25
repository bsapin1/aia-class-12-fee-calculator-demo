from __future__ import annotations

from calculators.drawing_fee import calculate_drawing_fee
from calculators.percentage_fee import (
    calculate_percentage_fee,
    effective_fee_percentage,
    get_market_range,
    resolve_total_fee,
)
from calculators.schedule import allocate_phase_fees, build_schedule
from calculators.staffing_fee import calculate_staffing_fee
from models.project import Project
from models.results import FeeComparison, FeeResult, ScheduleResult


def _variance(primary: float, other: float) -> float:
    if primary <= 0:
        return 0.0
    return ((other - primary) / primary) * 100.0


def run_calculations(project: Project) -> tuple[FeeResult, ScheduleResult, FeeComparison]:
    percentage_total = calculate_percentage_fee(project.construction_budget, project.fee_percentage)
    staffing_total = calculate_staffing_fee(project)
    drawing_total = calculate_drawing_fee(project.drawing_set)

    primary_total, primary_method = resolve_total_fee(
        project.construction_budget,
        project.fee_percentage,
        project.stipulated_sum,
        project.fee_method,
        percentage_total,
        staffing_total,
        drawing_total,
    )

    effective_pct = effective_fee_percentage(
        project.construction_budget,
        project.fee_percentage,
        project.stipulated_sum,
    )
    if primary_method == "staffing":
        effective_pct = (staffing_total / project.construction_budget) * 100.0
    elif primary_method == "per_drawing":
        effective_pct = (drawing_total / project.construction_budget) * 100.0

    phase_breakdown = allocate_phase_fees(project, primary_total)
    schedule_milestones = build_schedule(project, phase_breakdown)

    market_min, market_max, _ = get_market_range(project.project_type)
    in_range = market_min <= effective_pct <= market_max
    if in_range:
        market_message = f"Effective fee {effective_pct:.1f}% is within the market range ({market_min:.0f}–{market_max:.0f}%)."
    elif effective_pct < market_min:
        market_message = (
            f"Effective fee {effective_pct:.1f}% is below the typical market range "
            f"({market_min:.0f}–{market_max:.0f}%). Consider scope or risk adjustments."
        )
    else:
        market_message = (
            f"Effective fee {effective_pct:.1f}% is above the typical market range "
            f"({market_min:.0f}–{market_max:.0f}%). Verify complexity and service level."
        )

    notes: list[str] = []
    staffing_var = _variance(primary_total, staffing_total)
    drawing_var = _variance(primary_total, drawing_total)
    if abs(staffing_var) > 15:
        notes.append(f"Staffing build-up differs from primary fee by {staffing_var:+.1f}%.")
    if abs(drawing_var) > 15:
        notes.append(f"Per-drawing estimate differs from primary fee by {drawing_var:+.1f}%.")

    fee_result = FeeResult(
        method=primary_method,
        total_fee=primary_total,
        fee_as_pct_of_construction=effective_pct,
        phase_breakdown=phase_breakdown,
        notes=notes,
    )
    schedule_result = ScheduleResult(
        phases=phase_breakdown,
        milestones=schedule_milestones,
        total_weeks=project.total_weeks,
    )
    comparison = FeeComparison(
        percentage_fee=percentage_total,
        staffing_fee=staffing_total,
        drawing_fee=drawing_total,
        primary_fee=primary_total,
        primary_method=primary_method,
        variance_pct={
            "staffing": staffing_var,
            "drawing": drawing_var,
        },
        market_in_range=in_range,
        market_min_pct=market_min,
        market_max_pct=market_max,
        market_message=market_message,
    )
    return fee_result, schedule_result, comparison
