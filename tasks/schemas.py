from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    projectId: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    assigneeId: Optional[str] = None
    startDate: Optional[datetime] = None
    dueDate: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigneeId: Optional[str] = None
    startDate: Optional[datetime] = None
    dueDate: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: str
    createdBy: str
    createdAt: datetime

    class Config:
        from_attributes = True


class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class TaskCommentResponse(BaseModel):
    id: str
    taskId: str
    authorId: str
    content: str
    createdAt: datetime

    class Config:
        from_attributes = True
