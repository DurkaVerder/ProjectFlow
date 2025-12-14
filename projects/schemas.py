from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "ACTIVE"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    ownerId: str
    createdAt: datetime

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    userId: str


class ProjectMemberResponse(BaseModel):
    id: str
    projectId: str
    userId: str
    userName: Optional[str] = None
    addedAt: datetime

    class Config:
        from_attributes = True
