from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from schemas import TaskCreate, TaskUpdate, TaskResponse, TaskCommentCreate, TaskCommentResponse
from models import Task, TaskComment
from auth_utils import get_current_user
from kafka_producer import kafka_producer

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await kafka_producer.start()
    yield
    # Shutdown
    await kafka_producer.stop()

app = FastAPI(title="Tasks Service", lifespan=lifespan)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_task = Task(
        projectId=task.projectId,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigneeId=task.assigneeId,
        createdBy=current_user["id"],
        startDate=task.startDate,
        dueDate=task.dueDate
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Отправляем событие в Kafka
    if db_task.assigneeId:
        await kafka_producer.send_event('tasks-events', {
            'event_type': 'task_created',
            'task_id': str(db_task.id),
            'task_title': db_task.title,
            'assignee_id': str(db_task.assigneeId)
        })
    
    return TaskResponse(
        id=str(db_task.id),
        projectId=str(db_task.projectId),
        title=db_task.title,
        description=db_task.description,
        status=db_task.status,
        priority=db_task.priority,
        assigneeId=str(db_task.assigneeId) if db_task.assigneeId else None,
        createdBy=str(db_task.createdBy),
        startDate=db_task.startDate,
        dueDate=db_task.dueDate,
        createdAt=db_task.createdAt
    )


@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    project: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Task)
    
    if project:
        query = query.filter(Task.projectId == uuid.UUID(project))
    
    tasks = query.all()
    
    return [
        TaskResponse(
            id=str(t.id),
            projectId=str(t.projectId),
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            assigneeId=str(t.assigneeId) if t.assigneeId else None,
            createdBy=str(t.createdBy),
            startDate=t.startDate,
            dueDate=t.dueDate,
            createdAt=t.createdAt
        )
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(
        id=str(task.id),
        projectId=str(task.projectId),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigneeId=str(task.assigneeId) if task.assigneeId else None,
        createdBy=str(task.createdBy),
        startDate=task.startDate,
        dueDate=task.dueDate,
        createdAt=task.createdAt
    )


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.status is not None:
        task.status = task_update.status
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.assigneeId is not None:
        task.assigneeId = task_update.assigneeId
    if task_update.startDate is not None:
        task.startDate = task_update.startDate
    if task_update.dueDate is not None:
        task.dueDate = task_update.dueDate
    
    db.commit()
    db.refresh(task)
    
    # Отправляем событие в Kafka при обновлении
    if task.assigneeId:
        await kafka_producer.send_event('tasks-events', {
            'event_type': 'task_updated',
            'task_id': str(task.id),
            'task_title': task.title,
            'assignee_id': str(task.assigneeId)
        })
    
    return TaskResponse(
        id=str(task.id),
        projectId=str(task.projectId),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigneeId=str(task.assigneeId) if task.assigneeId else None,
        createdBy=str(task.createdBy),
        startDate=task.startDate,
        dueDate=task.dueDate,
        createdAt=task.createdAt
    )


@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@app.get("/tasks/{task_id}/comments", response_model=List[TaskCommentResponse])
async def get_task_comments(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    comments = db.query(TaskComment).filter(TaskComment.taskId == uuid.UUID(task_id)).all()
    
    return [
        TaskCommentResponse(
            id=str(c.id),
            taskId=str(c.taskId),
            authorId=str(c.authorId),
            content=c.content,
            createdAt=c.createdAt
        )
        for c in comments
    ]


@app.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse)
async def add_task_comment(
    task_id: str,
    comment: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db_comment = TaskComment(
        taskId=task_id,
        authorId=current_user["id"],
        content=comment.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    # Отправляем событие в Kafka
    if task.assigneeId:
        await kafka_producer.send_event('tasks-events', {
            'event_type': 'comment_added',
            'task_id': str(task.id),
            'task_title': task.title,
            'task_assignee_id': str(task.assigneeId)
        })
    
    return TaskCommentResponse(
        id=str(db_comment.id),
        taskId=str(db_comment.taskId),
        authorId=str(db_comment.authorId),
        content=db_comment.content,
        createdAt=db_comment.createdAt
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
