import httpx
import uuid
from config import settings

# Хранилище временных токенов для связывания пользователей
pending_connections = {}

async def send_telegram_notification(chat_id: str, message: str):
    """Отправка уведомления в Telegram"""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("Telegram bot token not configured, skipping telegram notification")
        return
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print(f"Telegram message sent successfully to {chat_id}")
            else:
                raise Exception(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")
        raise

def generate_telegram_deep_link(user_id: str, bot_username: str = None):
    """Генерация deep link для подключения Telegram бота"""
    if not bot_username:
        bot_username = "mos_polytech_course_work_bot" 
    
    # Генерируем уникальный токен для связывания
    connection_token = str(uuid.uuid4())
    pending_connections[connection_token] = {
        "user_id": user_id,
        "connected": False
    }
    
    # Deep link формата: https://t.me/bot_username?start=token
    deep_link = f"https://t.me/{bot_username}?start={connection_token}"
    
    return {
        "deep_link": deep_link,
        "connection_token": connection_token,
        "instructions": "Перейдите по ссылке и нажмите START в боте"
    }

async def handle_telegram_start(start_param: str, chat_id: str):
    """Обработка команды /start с параметром от бота"""
    if start_param in pending_connections:
        user_info = pending_connections[start_param]
        user_info["connected"] = True
        user_info["chat_id"] = str(chat_id)
        
        # Отправляем приветственное сообщение
        welcome_message = "✅ *Успешно подключено!*\n\nТеперь вы будете получать уведомления из ProjectFlow."
        await send_telegram_notification(str(chat_id), welcome_message)
        
        return user_info
    
    return None

def get_connection_status(connection_token: str):
    """Проверка статуса подключения"""
    if connection_token in pending_connections:
        return pending_connections[connection_token]
    return None

def cleanup_connection(connection_token: str):
    """Очистка завершенного подключения"""
    if connection_token in pending_connections:
        del pending_connections[connection_token]
