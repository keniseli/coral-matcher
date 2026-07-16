from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel
from app.embedding.embedding import EMBEDDING_DIMENSION

class Observation(SQLModel, table=True):
    __tablename__ = "observations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    embedding: list[float] = Field(
        description="L2-normalized embedding vector produced by the embedding model.",
        sa_column=Column(Vector(EMBEDDING_DIMENSION), nullable=False),
    )

    monitoring_session_id: uuid.UUID = Field(
        foreign_key="monitoring_sessions.id",
        nullable=False,
    )

    dive_site: str

    image_path: str

    image_filename: str

    image_width: int

    image_height: int

    crop_polygon: list[dict] = Field(
        sa_column=Column(JSONB, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.now(),
        nullable=False,
    )