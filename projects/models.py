from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="ACTIVE", nullable=False)
    ownerId = Column(UUID(as_uuid=True), nullable=False, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    projectId = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    userId = Column(UUID(as_uuid=True), nullable=False, index=True)
    addedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
