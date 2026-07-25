from pydantic import ConfigDict, Field
from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime

class DiveSiteResponse(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class MonitoringSessionResponse(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: UUID
    name: str | None
    timestamp: datetime

    dive_site: DiveSiteResponse = Field(
        serialization_alias="diveSite"
    )

    observation_count: int = Field(
        serialization_alias="observationCount"
    )