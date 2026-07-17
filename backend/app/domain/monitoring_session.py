from __future__ import annotations
from typing import TYPE_CHECKING

import uuid
from datetime import datetime

from app.domain.observation import Observation

from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from app.domain.observation import Observation

class MonitoringSession(SQLModel, table=True):
    __tablename__ = "monitoring_sessions"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    
    timestamp: datetime