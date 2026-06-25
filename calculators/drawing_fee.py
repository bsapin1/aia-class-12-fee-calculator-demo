from __future__ import annotations

from models.project import DrawingSet
from calculators.config_loader import get_complexity_multipliers, get_drawing_disciplines


def calculate_drawing_fee(drawing_set: DrawingSet) -> float:
    disciplines_config = get_drawing_disciplines()
    complexity_key = f"rate_per_sheet_{drawing_set.complexity}"
    multiplier = get_complexity_multipliers()[drawing_set.complexity]
    revision_factor = 1.0 + max(drawing_set.revision_rounds - 2, 0) * 0.05

    total = 0.0
    for discipline in drawing_set.disciplines:
        if discipline.sheet_count <= 0:
            continue
        config = disciplines_config.get(discipline.discipline_key)
        if not config:
            continue
        rate = config[complexity_key]
        total += discipline.sheet_count * rate * multiplier

    return total * revision_factor
