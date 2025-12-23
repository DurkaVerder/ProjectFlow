import httpx
import uuid
from config import settings


pending_connections = {}

async def send_telegram_notification(chat_id: str, message: str):

    if not settings.TELEGRAM_BOT_TOKEN:
        print("[Telegram] Bot token not configured, skipping telegram notification", flush=True)
        return
    
    url = f"https://api.telegram.org/bot8508817832:AAEg2G7SeklAHNk0JVdNfctqR-yJtLoSCbw/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    print(f"[Telegram] Sending message to chat_id={chat_id} with payload: {payload}", flush=True)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            print(f"[Telegram] Telegram API response status: {response.status_code}", flush=True)
            print(f"[Telegram] Telegram API response body: {response.text}", flush=True)
            if response.status_code == 200:
                print(f"[Telegram] Message sent successfully to {chat_id}", flush=True)
            else:
                raise Exception(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"[Telegram] Failed to send telegram message: {e}", flush=True)
        raise

def generate_telegram_deep_link(user_id: str, bot_username: str = None):
  
    if not bot_username:
        bot_username = "mos_polytech_course_work_bot" 
    
    connection_token = str(uuid.uuid4())
    pending_connections[connection_token] = {
        "user_id": user_id,
        "connected": False
    }
    
    deep_link = f"https://t.me/{bot_username}?start={connection_token}"
    
    return {
        "deep_link": deep_link,
        "connection_token": connection_token,
        "instructions": "Перейдите по ссылке и нажмите START в боте"
    }

async def handle_telegram_start(start_param: str, chat_id: str):
    if start_param in pending_connections:
        user_info = pending_connections[start_param]
        user_info["connected"] = True
        user_info["chat_id"] = str(chat_id)

        from database import SessionLocal
        from models import Integration
        import json
        db = SessionLocal()
        try:
           
            integrations = db.query(Integration).filter(
                Integration.userId == user_info["user_id"],
                Integration.integrationType == 'telegram'
            ).all()
            if integrations:
                for integration in integrations:
                    config = integration.config or {}
                    config["chat_id"] = str(chat_id)
                    integration.config = config
                db.commit()
                print(f"[Telegram] chat_id {chat_id} saved to {len(integrations)} Integration(s) for user_id {user_info['user_id']}", flush=True)
            else:
                print(f"[Telegram] No Integration found for user_id {user_info['user_id']} to save chat_id", flush=True)
        except Exception as e:
            print(f"[Telegram] Error saving chat_id to Integration: {e}", flush=True)
        finally:
            db.close()
        # ---

        welcome_message = "✅ *Успешно подключено!*\n\nТеперь вы будете получать уведомления из ProjectFlow."
        await send_telegram_notification(str(chat_id), welcome_message)
        return user_info
    return None

def get_connection_status(connection_token: str):
    if connection_token in pending_connections:
        return pending_connections[connection_token]
    return None

def cleanup_connection(connection_token: str):
    if connection_token in pending_connections:
        del pending_connections[connection_token]
