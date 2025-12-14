import asyncio
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Notification
from config import settings
import uuid

async def consume_kafka_messages():
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            consumer = AIOKafkaConsumer(
                'projects-events',
                'tasks-events',
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id='notifications-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            await consumer.start()
            print(f"Successfully connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            try:
                async for message in consumer:
                    await process_message(message.value, message.topic)
            finally:
                await consumer.stop()
            return
        except KafkaConnectionError:
            if attempt < max_retries - 1:
                print(f"Kafka connection attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print("Failed to connect to Kafka after all retries")
                raise

async def process_message(data: dict, topic: str):
    db: Session = SessionLocal()
    try:
        event_type = data.get('event_type')
        
        # Определяем тип уведомления и создаем сообщение
        notification_data = create_notification_data(event_type, data, topic)
        
        if notification_data:
            notification = Notification(**notification_data)
            db.add(notification)
            db.commit()
    except Exception as e:
        print(f"Error processing message: {e}")
        db.rollback()
    finally:
        db.close()

def create_notification_data(event_type: str, data: dict, topic: str) -> dict:
    """Создает данные для уведомления на основе типа события"""
    
    if topic == 'projects-events':
        if event_type == 'project_created':
            return {
                'userId': uuid.UUID(data['owner_id']),
                'type': 'project_created',
                'title': 'Новый проект создан',
                'message': f"Проект '{data['project_name']}' был успешно создан"
            }
        elif event_type == 'member_added':
            return {
                'userId': uuid.UUID(data['user_id']),
                'type': 'member_added',
                'title': 'Вы добавлены в проект',
                'message': f"Вы были добавлены в проект '{data['project_name']}'"
            }
        elif event_type == 'member_removed':
            return {
                'userId': uuid.UUID(data['user_id']),
                'type': 'member_removed',
                'title': 'Вы удалены из проекта',
                'message': f"Вы были удалены из проекта '{data['project_name']}'"
            }
    
    elif topic == 'tasks-events':
        if event_type == 'task_created':
            if data.get('assignee_id'):
                return {
                    'userId': uuid.UUID(data['assignee_id']),
                    'type': 'task_assigned',
                    'title': 'Вам назначена задача',
                    'message': f"Задача '{data['task_title']}' была вам назначена"
                }
        elif event_type == 'task_updated':
            if data.get('assignee_id'):
                return {
                    'userId': uuid.UUID(data['assignee_id']),
                    'type': 'task_updated',
                    'title': 'Задача обновлена',
                    'message': f"Задача '{data['task_title']}' была обновлена"
                }
        elif event_type == 'comment_added':
            if data.get('task_assignee_id'):
                return {
                    'userId': uuid.UUID(data['task_assignee_id']),
                    'type': 'comment_added',
                    'title': 'Новый комментарий',
                    'message': f"Добавлен комментарий к задаче '{data['task_title']}'"
                }
    
    return None
