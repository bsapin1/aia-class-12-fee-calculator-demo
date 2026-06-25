from __future__ import annotations

from calculators.config_loader import get_phases, get_project_type_config


def calculate_percentage_fee(construction_budget: float, fee_percentage: float) -> float:
    return construction_budget * (fee_percentage / 100.0)


def effective_fee_percentage(
    construction_budget: float,
    fee_percentage: float | None,
    stipulated_sum: float | None,
) -> float:
    if stipulated_sum is not None and stipulated_sum > 0:
        return (stipulated_sum / construction_budget) * 100.0
    return fee_percentage or 0.0


def resolve_total_fee(
    construction_budget: float,
    fee_percentage: float,
    stipulated_sum: float | None,
    fee_method: str,
    percentage_total: float,
    staffing_total: float,
    drawing_total: float,
) -> tuple[float, str]:
    if fee_method == "stipulated_sum" and stipulated_sum:
        return stipulated_sum, "stipulated_sum"
    if fee_method == "staffing" and staffing_total > 0:
        return staffing_total, "staffing"
    if fee_method == "per_drawing" and drawing_total > 0:
        return drawing_total, "per_drawing"
    return percentage_total, "percentage"


def get_market_range(project_type: str) -> tuple[float, float, float]:
    config = get_project_type_config(project_type)
    return config["fee_pct_min"], config["fee_pct_max"], config["fee_pct_default"]
