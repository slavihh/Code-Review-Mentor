from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from enum import Enum
from app.core.db import Base


class Language(Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    JAVA = "Java"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
    )
    title = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    mongo_id = Column(String(64), nullable=True, unique=True)
    language = Column(SqlEnum(Language), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
