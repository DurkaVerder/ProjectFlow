from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProjectEventResponse(BaseModel):
    id: UUID
    eventType: str
    projectId: UUID
    projectName: Optional[str]
    ownerId: Optional[UUID]
    userId: Optional[UUID]
    createdAt: datetime

    class Config:
        from_attributes = True

class TaskEventResponse(BaseModel):
    id: UUID
    eventType: str
    taskId: UUID
    taskTitle: Optional[str]
    assigneeId: Optional[UUID]
    createdAt: datetime

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    id: UUID
    metricName: str
    metricValue: int
    period: Optional[str]
    calculatedAt: datetime

    class Config:
        from_attributes = True

class ProjectStats(BaseModel):
    totalProjects: int
    totalMembers: int
    projectsThisWeek: int

class TaskStats(BaseModel):
    totalTasks: int
    assignedTasks: int
    tasksThisWeek: int
    commentsThisWeek: int

class UserActivityStats(BaseModel):
    userId: UUID
    projectsCreated: int
    tasksAssigned: int
    commentsAdded: int
