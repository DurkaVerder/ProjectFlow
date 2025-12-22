from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uuid
import uvicorn
from contextlib import asynccontextmanager
import asyncio

from database import get_db, Base, engine
from models import Notification
from schemas import NotificationResponse
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

app = FastAPI(title="Notifications Service", lifespan=lifespan)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Notifications Service"}

@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить все уведомления пользователя"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Проверяем, что пользователь запрашивает свои уведомления
    if str(current_user["id"]) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    notifications = db.query(Notification).filter(
        Notification.userId == user_uuid
    ).order_by(Notification.createdAt.desc()).all()
    
    return notifications

@app.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Отметить уведомление как прочитанное"""
    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")
    
    notification = db.query(Notification).filter(
        Notification.id == notif_uuid
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Проверяем, что уведомление принадлежит текущему пользователю
    if str(notification.userId) != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    notification.isRead = True
    db.commit()
    db.refresh(notification)
    
    return notification

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
