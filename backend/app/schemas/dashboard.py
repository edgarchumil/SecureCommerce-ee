from datetime import date

from pydantic import BaseModel, Field


class Metric(BaseModel):
    key: str
    label: str
    value: float
    unit: str | None = None


class ChartPoint(BaseModel):
    key: str
    label: str
    value: float


class DashboardFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    asset_type: str | None = None


class DashboardResponse(BaseModel):
    filters: DashboardFilters
    kpis: list[Metric] = Field(min_length=4)
    assets_by_type: list[ChartPoint]
    risks_by_level: list[ChartPoint]
    evaluations_by_status: list[ChartPoint]
    risks_over_time: list[ChartPoint]
