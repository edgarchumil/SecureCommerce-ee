from typing import Literal

from pydantic import BaseModel


class DependencyStatus(BaseModel):
    status: Literal["ok", "error"]


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    services: dict[str, DependencyStatus]
