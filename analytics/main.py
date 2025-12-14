from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import uuid
import uvicorn
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta

from database import get_db, Base, engine
from models import ProjectEvent, TaskEvent, Analytics
from schemas import (
    ProjectEventResponse, TaskEventResponse, AnalyticsResponse,
    ProjectStats, TaskStats, UserActivityStats
)
from auth_utils import get_current_user, security
from kafka_consumer import consume_kafka_messages

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Глобальная переменная для задачи Kafka
kafka_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: запускаем Kafka consumer
    global kafka_task
    kafka_task = asyncio.create_task(consume_kafka_messages())
    yield
    # Shutdown: останавливаем Kafka consumer
    if kafka_task:
        kafka_task.cancel()
        try:
            await kafka_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="Analytics Service", lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Analytics Service"}

@app.get("/analytics/projects/stats", response_model=ProjectStats)
async def get_project_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить общую статистику по проектам"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    total_projects = db.query(ProjectEvent).filter(
        ProjectEvent.eventType == 'project_created'
    ).count()
    
    total_members = db.query(ProjectEvent).filter(
        ProjectEvent.eventType == 'member_added'
    ).count()
    
    projects_this_week = db.query(ProjectEvent).filter(
        ProjectEvent.eventType == 'project_created',
        ProjectEvent.createdAt >= week_ago
    ).count()
    
    return ProjectStats(
        totalProjects=total_projects,
        totalMembers=total_members,
        projectsThisWeek=projects_this_week
    )

@app.get("/analytics/tasks/stats", response_model=TaskStats)
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить общую статистику по задачам"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    total_tasks = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'task_created'
    ).count()
    
    assigned_tasks = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'task_created',
        TaskEvent.assigneeId.isnot(None)
    ).count()
    
    tasks_this_week = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'task_created',
        TaskEvent.createdAt >= week_ago
    ).count()
    
    comments_this_week = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'comment_added',
        TaskEvent.createdAt >= week_ago
    ).count()
    
    return TaskStats(
        totalTasks=total_tasks,
        assignedTasks=assigned_tasks,
        tasksThisWeek=tasks_this_week,
        commentsThisWeek=comments_this_week
    )

@app.get("/analytics/user/{user_id}/activity", response_model=UserActivityStats)
async def get_user_activity(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить активность конкретного пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    projects_created = db.query(ProjectEvent).filter(
        ProjectEvent.eventType == 'project_created',
        ProjectEvent.ownerId == user_uuid
    ).count()
    
    tasks_assigned = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'task_created',
        TaskEvent.assigneeId == user_uuid
    ).count()
    
    # Для комментариев используем userId из ProjectEvent (когда member_added)
    # Это приблизительная оценка активности
    comments_added = db.query(TaskEvent).filter(
        TaskEvent.eventType == 'comment_added'
    ).count()
    
    return UserActivityStats(
        userId=user_uuid,
        projectsCreated=projects_created,
        tasksAssigned=tasks_assigned,
        commentsAdded=comments_added
    )

@app.get("/analytics/projects/events", response_model=List[ProjectEventResponse])
async def get_project_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить последние события проектов"""
    events = db.query(ProjectEvent).order_by(
        ProjectEvent.createdAt.desc()
    ).limit(limit).all()
    
    return events

@app.get("/analytics/tasks/events", response_model=List[TaskEventResponse])
async def get_task_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить последние события задач"""
    events = db.query(TaskEvent).order_by(
        TaskEvent.createdAt.desc()
    ).limit(limit).all()
    
    return events

@app.get("/analytics/projects/{project_id}/activity", response_model=List[ProjectEventResponse])
async def get_project_activity(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить всю активность по конкретному проекту"""
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    events = db.query(ProjectEvent).filter(
        ProjectEvent.projectId == proj_uuid
    ).order_by(ProjectEvent.createdAt.desc()).all()
    
    return events

@app.get("/analytics/tasks/{task_id}/activity", response_model=List[TaskEventResponse])
async def get_task_activity(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить всю активность по конкретной задаче"""
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    
    events = db.query(TaskEvent).filter(
        TaskEvent.taskId == task_uuid
    ).order_by(TaskEvent.createdAt.desc()).all()
    
    return events

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
