import asyncio
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Integration, WebhookLog
from config import settings
import uuid
from email_service import send_email_notification
from telegram_service import send_telegram_notification

async def consume_kafka_messages():
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            consumer = AIOKafkaConsumer(
                'projects-events',
                'tasks-events',
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id='integrations-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            await consumer.start()
            print(f"Integrations: Successfully connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
            
            try:
                async for message in consumer:
                    await process_message(message.value, message.topic)
            finally:
                await consumer.stop()
            return
        except KafkaConnectionError:
            if attempt < max_retries - 1:
                print(f"Integrations Kafka connection attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print("Integrations: Failed to connect to Kafka after all retries")
                raise

async def process_message(data: dict, topic: str):
    db: Session = SessionLocal()
    try:
        event_type = data.get('event_type')
        
        # Находим активные интеграции
        integrations = db.query(Integration).filter(
            Integration.isActive == True
        ).all()
        
        for integration in integrations:
            await send_to_integration(integration, event_type, data, db)
    
    except Exception as e:
        print(f"Error processing integrations message: {e}")
    finally:
        db.close()

async def send_to_integration(integration: Integration, event_type: str, data: dict, db: Session):
    try:
        if integration.integrationType == 'email':
            config = integration.config
            if config.get('email'):
                subject = f"ProjectFlow: {event_type}"
                body = f"Event occurred: {event_type}\nDetails: {json.dumps(data, indent=2)}"
                await send_email_notification(config['email'], subject, body)
                
                log = WebhookLog(
                    integrationId=integration.id,
                    eventType=event_type,
                    payload=data,
                    status='success'
                )
                db.add(log)
                db.commit()
        
        elif integration.integrationType == 'telegram':
            config = integration.config
            if config.get('chat_id'):
                message = f"🔔 *{event_type}*\n\n{json.dumps(data, indent=2)}"
                await send_telegram_notification(config['chat_id'], message)
                
                log = WebhookLog(
                    integrationId=integration.id,
                    eventType=event_type,
                    payload=data,
                    status='success'
                )
                db.add(log)
                db.commit()
    
    except Exception as e:
        log = WebhookLog(
            integrationId=integration.id,
            eventType=event_type,
            payload=data,
            status='failed',
            errorMessage=str(e)
        )
        db.add(log)
        db.commit()
        print(f"Failed to send to integration {integration.id}: {e}")
