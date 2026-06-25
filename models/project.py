from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ProjectType = Literal[
    "custom_residential",
    "residential_renovation",
    "commercial_office",
    "institutional",
    "warehouse_shell",
]
RegionTier = Literal["premium", "high", "medium", "standard", "value"]
Complexity = Literal["simple", "standard", "complex"]
FeeMethod = Literal["percentage", "staffing", "per_drawing", "stipulated_sum"]


class StaffMember(BaseModel):
    role_key: str
    role_label: str
    hourly_rate: float = Field(gt=0)
    hours_sd: float = Field(ge=0, default=0)
    hours_dd: float = Field(ge=0, default=0)
    hours_cd: float = Field(ge=0, default=0)
    hours_bidding: float = Field(ge=0, default=0)
    hours_ca: float = Field(ge=0, default=0)

    @property
    def total_hours(self) -> float:
        return self.hours_sd + self.hours_dd + self.hours_cd + self.hours_bidding + self.hours_ca

    @property
    def total_cost(self) -> float:
        return self.total_hours * self.hourly_rate


class DrawingDiscipline(BaseModel):
    discipline_key: str
    discipline_label: str
    sheet_count: int = Field(ge=0, default=0)


class DrawingSet(BaseModel):
    disciplines: list[DrawingDiscipline] = Field(default_factory=list)
    complexity: Complexity = "standard"
    revision_rounds: int = Field(ge=0, default=2)

    @property
    def total_sheets(self) -> int:
        return sum(d.sheet_count for d in self.disciplines)


class Milestone(BaseModel):
    name: str
    phase_key: str
    week_offset: float = Field(ge=0)
    fee_pct_of_phase: float = Field(ge=0, le=100, default=100)


class Project(BaseModel):
    name: str = "Untitled Project"
    project_type: ProjectType = "custom_residential"
    region: RegionTier = "medium"
    construction_budget: float = Field(gt=0, default=1_000_000)
    fee_percentage: float = Field(gt=0, le=30, default=10.0)
    fee_method: FeeMethod = "percentage"
    stipulated_sum: float | None = None
    start_date: date = Field(default_factory=date.today)
    total_weeks: int = Field(gt=0, default=40)
    include_ca: bool = True
    include_bidding: bool = True
    phase_fee_pcts: dict[str, float] = Field(default_factory=dict)
    phase_duration_pcts: dict[str, float] = Field(default_factory=dict)
    staff: list[StaffMember] = Field(default_factory=list)
    drawing_set: DrawingSet = Field(default_factory=DrawingSet)
    custom_milestones: list[Milestone] = Field(default_factory=list)
    description: str = ""

    @field_validator("phase_fee_pcts", "phase_duration_pcts")
    @classmethod
    def validate_pct_dict(cls, value: dict[str, float]) -> dict[str, float]:
        if value and abs(sum(value.values()) - 100.0) > 0.01:
            raise ValueError("Phase percentages must sum to 100")
        return value
