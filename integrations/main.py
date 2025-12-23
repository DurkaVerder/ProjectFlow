from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uuid
import uvicorn
from contextlib import asynccontextmanager
import asyncio

from database import get_db, Base, engine
from models import Integration, WebhookLog, GitHubRepository
from schemas import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse,
    WebhookLogResponse, GitHubRepoCreate, GitHubRepoResponse,
    EmailNotification, TelegramNotification, TelegramConnectionResponse,
    TelegramWebhook, GitHubIssueCreate
)
from auth_utils import get_current_user, security
from kafka_consumer import consume_kafka_messages
from email_service import send_email_notification
from telegram_service import (
    send_telegram_notification, generate_telegram_deep_link,
    handle_telegram_start, get_connection_status, cleanup_connection
)
from github_service import create_github_issue, get_github_issues

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

app = FastAPI(title="Integrations Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Integrations Service"}





@app.post("/integrations/telegram/connect", response_model=TelegramConnectionResponse)
async def connect_telegram(
    current_user: dict = Depends(get_current_user)
):
    """Получить deep link для подключения Telegram бота"""
    try:
        result = generate_telegram_deep_link(
            user_id=current_user["id"],
            bot_username="mos_polytech_course_work_bot"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate link: {str(e)}")

@app.get("/integrations/telegram/status/{connection_token}")
async def check_telegram_connection(
    connection_token: str,
    current_user: dict = Depends(get_current_user)
):
  
    status = get_connection_status(connection_token)
    
    if not status:
        raise HTTPException(status_code=404, detail="Connection token not found")
    
    if status["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "connected": status.get("connected", False),
        "chat_id": status.get("chat_id") if status.get("connected") else None
    }

@app.post("/integrations/telegram/webhook")
async def telegram_webhook(webhook_data: TelegramWebhook):

    try:
        message = webhook_data.message
        if not message:
            return {"ok": True}
        
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        
    
        if text.startswith("/start "):
            start_param = text.split(" ")[1]
            result = await handle_telegram_start(start_param, chat_id)
            
            if result:
                return {"ok": True, "status": "connected"}
        
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/integrations/telegram/send")
async def send_telegram(
    telegram_data: TelegramNotification,
    current_user: dict = Depends(get_current_user)
):

    try:
        await send_telegram_notification(telegram_data.chatId, telegram_data.message)
        return {"message": "Telegram message sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send telegram message: {str(e)}")

