import asyncio
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ProjectEvent, TaskEvent
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
                group_id='analytics-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            await consumer.start()
            print(f"Analytics: Successfully connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            try:
                async for message in consumer:
                    await process_message(message.value, message.topic)
            finally:
                await consumer.stop()
            return
        except KafkaConnectionError:
            if attempt < max_retries - 1:
                print(f"Analytics Kafka connection attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print("Analytics: Failed to connect to Kafka after all retries")
                raise

async def process_message(data: dict, topic: str):
    db: Session = SessionLocal()
    try:
        event_type = data.get('event_type')
        
        if topic == 'projects-events':
            event = ProjectEvent(
                eventType=event_type,
                projectId=uuid.UUID(data['project_id']),
                projectName=data.get('project_name'),
                ownerId=uuid.UUID(data['owner_id']) if data.get('owner_id') else None,
                userId=uuid.UUID(data['user_id']) if data.get('user_id') else None
            )
            db.add(event)
            db.commit()
            print(f"Saved project event: {event_type}")
        
        elif topic == 'tasks-events':
            event = TaskEvent(
                eventType=event_type,
                taskId=uuid.UUID(data['task_id']),
                taskTitle=data.get('task_title'),
                assigneeId=uuid.UUID(data['assignee_id']) if data.get('assignee_id') else None
            )
            db.add(event)
            db.commit()
            print(f"Saved task event: {event_type}")
    
    except Exception as e:
        print(f"Error processing analytics message: {e}")
        db.rollback()
    finally:
        db.close()
