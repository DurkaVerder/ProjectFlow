from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any

class IntegrationCreate(BaseModel):
    projectId: Optional[UUID] = None
    integrationType: str  # email, telegram, github
    config: Dict[str, Any]

class IntegrationUpdate(BaseModel):
    isActive: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

class IntegrationResponse(BaseModel):
    id: UUID
    userId: UUID
    projectId: Optional[UUID]
    integrationType: str
    isActive: bool
    config: Dict[str, Any]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class WebhookLogResponse(BaseModel):
    id: UUID
    integrationId: UUID
    eventType: str
    payload: Dict[str, Any]
    status: str
    errorMessage: Optional[str]
    createdAt: datetime

    class Config:
        from_attributes = True

class GitHubRepoCreate(BaseModel):
    projectId: UUID
    repositoryUrl: str
    accessToken: Optional[str] = None
    syncEnabled: bool = False

class GitHubRepoResponse(BaseModel):
    id: UUID
    projectId: UUID
    repositoryUrl: str
    syncEnabled: bool
    lastSyncAt: Optional[datetime]
    createdAt: datetime

    class Config:
        from_attributes = True

class EmailNotification(BaseModel):
    to: EmailStr
    subject: str
    body: str

class TelegramNotification(BaseModel):
    chatId: str
    message: str

class TelegramConnectionResponse(BaseModel):
    deep_link: str
    connection_token: str
    instructions: str

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None

class GitHubIssueCreate(BaseModel):
    repositoryUrl: str
    title: str
    body: str
    accessToken: str
