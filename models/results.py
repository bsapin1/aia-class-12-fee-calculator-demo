from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PhaseResult(BaseModel):
    phase_key: str
    phase_label: str
    fee_pct: float
    fee_amount: float
    duration_weeks: float
    start_date: date
    end_date: date


class FeeResult(BaseModel):
    method: str
    total_fee: float
    fee_as_pct_of_construction: float
    phase_breakdown: list[PhaseResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ScheduleResult(BaseModel):
    phases: list[PhaseResult]
    milestones: list[dict] = Field(default_factory=list)
    total_weeks: float


class FeeComparison(BaseModel):
    percentage_fee: float
    staffing_fee: float
    drawing_fee: float
    primary_fee: float
    primary_method: str
    variance_pct: dict[str, float] = Field(default_factory=dict)
    market_in_range: bool
    market_min_pct: float
    market_max_pct: float
    market_message: str
