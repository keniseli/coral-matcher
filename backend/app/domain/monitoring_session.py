from __future__ import annotations

import uuid
from datetime import datetime

from app.domain.observation import Observation

from sqlmodel import Field, Relationship, SQLModel


class MonitoringSession(SQLModel, table=True):
    __tablename__ = "monitoring_sessions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    observations: list["Observation"] = Relationship(
        back_populates="monitoring_session"
    )
    
    timestamp: datetime