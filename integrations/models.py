from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid
from datetime import datetime

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), nullable=False)
    projectId = Column(UUID(as_uuid=True))
    integrationType = Column(String(50), nullable=False)  
    isActive = Column(Boolean, default=True)
    config = Column(JSON)  
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integrationId = Column(UUID(as_uuid=True), nullable=False)
    eventType = Column(String(50), nullable=False)
    payload = Column(JSON)
    status = Column(String(20))  # success, failed
    errorMessage = Column(Text)
    createdAt = Column(DateTime, default=datetime.utcnow)

class GitHubRepository(Base):
    __tablename__ = "github_repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), nullable=False)
    repositoryUrl = Column(String(500), nullable=False)
    accessToken = Column(String(500))
    syncEnabled = Column(Boolean, default=False)
    lastSyncAt = Column(DateTime)
    createdAt = Column(DateTime, default=datetime.utcnow)
