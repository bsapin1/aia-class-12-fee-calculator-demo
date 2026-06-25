from __future__ import annotations

from models.project import Project, StaffMember
from calculators.config_loader import get_overhead_multiplier, get_region_config, get_staff_roles


PHASE_HOUR_KEYS = ("hours_sd", "hours_dd", "hours_cd", "hours_bidding", "hours_ca")


def default_staff_for_project(project_type: str, region: str, total_weeks: int) -> list[StaffMember]:
    roles = get_staff_roles()
    multiplier = get_region_config(region)["hourly_multiplier"]
    scale = max(total_weeks / 40.0, 0.5)

    defaults = {
        "principal": (40, 30, 20, 10, 60),
        "project_architect": (80, 100, 200, 20, 80),
        "project_manager": (60, 80, 120, 40, 100),
        "designer": (120, 160, 320, 10, 40),
        "intern": (80, 100, 200, 0, 20),
    }

    staff: list[StaffMember] = []
    for role_key, hours in defaults.items():
        role = roles[role_key]
        scaled = tuple(h * scale for h in hours)
        staff.append(
            StaffMember(
                role_key=role_key,
                role_label=role["label"],
                hourly_rate=round(role["base_hourly"] * multiplier, 2),
                hours_sd=scaled[0],
                hours_dd=scaled[1],
                hours_cd=scaled[2],
                hours_bidding=scaled[3],
                hours_ca=scaled[4],
            )
        )
    return staff


def calculate_staffing_fee(project: Project) -> float:
    direct_labor = sum(member.total_cost for member in project.staff)
    return direct_labor * get_overhead_multiplier()


def staffing_hours_by_phase(project: Project) -> dict[str, float]:
    return {
        "schematic_design": sum(m.hours_sd for m in project.staff),
        "design_development": sum(m.hours_dd for m in project.staff),
        "construction_documents": sum(m.hours_cd for m in project.staff),
        "bidding": sum(m.hours_bidding for m in project.staff),
        "construction_admin": sum(m.hours_ca for m in project.staff),
    }
