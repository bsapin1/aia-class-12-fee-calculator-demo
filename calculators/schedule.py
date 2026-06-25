from __future__ import annotations

from datetime import date, timedelta

from calculators.config_loader import get_phases
from models.project import Project
from models.results import PhaseResult


def _active_phases(project: Project) -> list[tuple[str, dict]]:
    phases = get_phases()
    active = []
    for key, config in phases.items():
        if key == "bidding" and not project.include_bidding:
            continue
        if key == "construction_admin" and not project.include_ca:
            continue
        active.append((key, config))
    return active


def _normalized_pcts(project: Project, kind: str) -> dict[str, float]:
    phases = _active_phases(project)
    source = project.phase_fee_pcts if kind == "fee" else project.phase_duration_pcts
    defaults = get_phases()

    raw = {}
    for key, _ in phases:
        if source and key in source:
            raw[key] = source[key]
        else:
            raw[key] = defaults[key]["fee_pct" if kind == "fee" else "duration_pct"]

    total = sum(raw.values())
    if total <= 0:
        return {key: 100.0 / len(phases) for key, _ in phases}
    return {key: (value / total) * 100.0 for key, value in raw.items()}


def allocate_phase_fees(project: Project, total_fee: float) -> list[PhaseResult]:
    fee_pcts = _normalized_pcts(project, "fee")
    duration_pcts = _normalized_pcts(project, "duration")
    phases = get_phases()

    current = project.start_date
    results: list[PhaseResult] = []
    for key, config in _active_phases(project):
        duration_weeks = project.total_weeks * (duration_pcts[key] / 100.0)
        end = current + timedelta(days=round(duration_weeks * 7))
        results.append(
            PhaseResult(
                phase_key=key,
                phase_label=config["label"],
                fee_pct=fee_pcts[key],
                fee_amount=total_fee * (fee_pcts[key] / 100.0),
                duration_weeks=round(duration_weeks, 1),
                start_date=current,
                end_date=end,
            )
        )
        current = end + timedelta(days=1)
    return results


def build_schedule(project: Project, phase_results: list[PhaseResult]) -> list[dict]:
    milestones: list[dict] = []
    for phase in phase_results:
        milestones.append(
            {
                "Milestone": f"{phase.phase_label} — Start",
                "Phase": phase.phase_label,
                "Date": phase.start_date.isoformat(),
                "Fee ($)": "",
                "Type": "Phase Start",
            }
        )
        milestones.append(
            {
                "Milestone": f"{phase.phase_label} — Complete",
                "Phase": phase.phase_label,
                "Date": phase.end_date.isoformat(),
                "Fee ($)": f"${phase.fee_amount:,.0f}",
                "Type": "Phase Complete",
            }
        )

    for custom in project.custom_milestones:
        milestone_date = project.start_date + timedelta(days=round(custom.week_offset * 7))
        milestones.append(
            {
                "Milestone": custom.name,
                "Phase": custom.phase_key,
                "Date": milestone_date.isoformat(),
                "Fee ($)": "",
                "Type": "Custom",
            }
        )

    milestones.sort(key=lambda row: row["Date"])
    return milestones
