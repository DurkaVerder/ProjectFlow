from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime

class ProjectEvent(Base):
    __tablename__ = "project_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eventType = Column(String(50), nullable=False)
    projectId = Column(UUID(as_uuid=True), nullable=False)
    projectName = Column(String(255))
    ownerId = Column(UUID(as_uuid=True))
    userId = Column(UUID(as_uuid=True))
    createdAt = Column(DateTime, default=datetime.utcnow)

class TaskEvent(Base):
    __tablename__ = "task_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eventType = Column(String(50), nullable=False)
    taskId = Column(UUID(as_uuid=True), nullable=False)
    taskTitle = Column(String(255))
    assigneeId = Column(UUID(as_uuid=True))
    createdAt = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metricName = Column(String(100), nullable=False)
    metricValue = Column(Integer, nullable=False)
    period = Column(String(50))  # daily, weekly, monthly
    calculatedAt = Column(DateTime, default=datetime.utcnow)
