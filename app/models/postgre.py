from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, func, Integer, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Language(str, Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    JAVA = "Java"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    short_feedback: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=False
    )
    mongo_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    language: Mapped[Language] = mapped_column(
        SqlEnum(Language), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
