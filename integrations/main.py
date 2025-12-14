from fastapi import FastAPI, Depends, HTTPException
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

@app.get("/")
def read_root():
    return {"message": "Integrations Service"}

# ========== CRUD для интеграций ==========

@app.post("/integrations", response_model=IntegrationResponse)
async def create_integration(
    integration: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Создать новую интеграцию"""
    db_integration = Integration(
        userId=uuid.UUID(current_user["id"]),
        projectId=integration.projectId,
        integrationType=integration.integrationType,
        config=integration.config
    )
    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    
    return db_integration

@app.get("/integrations", response_model=List[IntegrationResponse])
async def get_integrations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить все интеграции пользователя"""
    integrations = db.query(Integration).filter(
        Integration.userId == uuid.UUID(current_user["id"])
    ).all()
    
    return integrations

@app.get("/integrations/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить интеграцию по ID"""
    try:
        int_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")
    
    integration = db.query(Integration).filter(
        Integration.id == int_uuid,
        Integration.userId == uuid.UUID(current_user["id"])
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return integration

@app.put("/integrations/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    integration_update: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить интеграцию"""
    try:
        int_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")
    
    integration = db.query(Integration).filter(
        Integration.id == int_uuid,
        Integration.userId == uuid.UUID(current_user["id"])
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if integration_update.isActive is not None:
        integration.isActive = integration_update.isActive
    if integration_update.config is not None:
        integration.config = integration_update.config
    
    db.commit()
    db.refresh(integration)
    
    return integration

@app.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Удалить интеграцию"""
    try:
        int_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")
    
    integration = db.query(Integration).filter(
        Integration.id == int_uuid,
        Integration.userId == uuid.UUID(current_user["id"])
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    db.delete(integration)
    db.commit()
    
    return {"message": "Integration deleted successfully"}

# ========== Webhook logs ==========

@app.get("/integrations/{integration_id}/logs", response_model=List[WebhookLogResponse])
async def get_integration_logs(
    integration_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить логи webhook интеграции"""
    try:
        int_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID format")
    
    logs = db.query(WebhookLog).filter(
        WebhookLog.integrationId == int_uuid
    ).order_by(WebhookLog.createdAt.desc()).limit(limit).all()
    
    return logs

# ========== Email интеграция ==========

@app.post("/integrations/email/send")
async def send_email(
    email_data: EmailNotification,
    current_user: dict = Depends(get_current_user)
):
    """Отправить email уведомление"""
    try:
        await send_email_notification(email_data.to, email_data.subject, email_data.body)
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

# ========== Telegram интеграция ==========

@app.post("/integrations/telegram/connect", response_model=TelegramConnectionResponse)
async def connect_telegram(
    current_user: dict = Depends(get_current_user)
):
    """Получить deep link для подключения Telegram бота"""
    try:
        # TODO: Замените YOUR_BOT_USERNAME на реальный username вашего бота
        result = generate_telegram_deep_link(
            user_id=current_user["id"],
            bot_username="YOUR_BOT_USERNAME"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate link: {str(e)}")

@app.get("/integrations/telegram/status/{connection_token}")
async def check_telegram_connection(
    connection_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Проверить статус подключения Telegram"""
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
    """Webhook для получения обновлений от Telegram бота"""
    try:
        message = webhook_data.message
        if not message:
            return {"ok": True}
        
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        
        # Обрабатываем команду /start с параметром
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
    """Отправить Telegram уведомление"""
    try:
        await send_telegram_notification(telegram_data.chatId, telegram_data.message)
        return {"message": "Telegram message sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send telegram message: {str(e)}")

# ========== GitHub интеграция ==========

@app.post("/integrations/github/repositories", response_model=GitHubRepoResponse)
async def add_github_repository(
    repo: GitHubRepoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Добавить GitHub репозиторий к проекту"""
    db_repo = GitHubRepository(
        projectId=repo.projectId,
        repositoryUrl=repo.repositoryUrl,
        accessToken=repo.accessToken,
        syncEnabled=repo.syncEnabled
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    
    return db_repo

@app.get("/integrations/github/repositories/{project_id}", response_model=List[GitHubRepoResponse])
async def get_github_repositories(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить GitHub репозитории проекта"""
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID format")
    
    repos = db.query(GitHubRepository).filter(
        GitHubRepository.projectId == proj_uuid
    ).all()
    
    return repos

@app.post("/integrations/github/issues")
async def create_issue(
    issue_data: GitHubIssueCreate,
    current_user: dict = Depends(get_current_user)
):
    """Создать issue в GitHub"""
    try:
        # Парсим URL репозитория
        parts = issue_data.repositoryUrl.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid repository URL")
        
        owner, repo = parts[0], parts[1]
        
        issue = await create_github_issue(
            owner, repo,
            issue_data.title,
            issue_data.body,
            issue_data.accessToken
        )
        
        return issue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create GitHub issue: {str(e)}")

@app.get("/integrations/github/issues/{repo_owner}/{repo_name}")
async def get_issues(
    repo_owner: str,
    repo_name: str,
    access_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить issues из GitHub"""
    try:
        issues = await get_github_issues(repo_owner, repo_name, access_token)
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get GitHub issues: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
