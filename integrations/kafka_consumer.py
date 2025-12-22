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
            print(f"[Kafka] Integrations: Successfully connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}", flush=True)
            try:
                print("[Kafka] Consumer started, waiting for messages...", flush=True)
                async for message in consumer:
                    print(f"[Kafka] Received message from topic '{message.topic}': {message.value}", flush=True)
                    await process_message(message.value, message.topic)
            finally:
                print("[Kafka] Stopping consumer...", flush=True)
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
        print(f"[Process] Start processing message: {data} (topic: {topic})", flush=True)
        event_type = data.get('event_type')
        # Находим активные интеграции
        integrations = db.query(Integration).filter(
            Integration.isActive == True
        ).all()
        print(f"[Process] Found {len(integrations)} active integrations.", flush=True)
        for integration in integrations:
            print(f"[Process] Sending event '{event_type}' to integration {integration.id} of type {integration.integrationType}", flush=True)
            await send_to_integration(integration, event_type, data, db)
    except Exception as e:
        print(f"[Process] Error processing integrations message: {e}", flush=True)
    finally:
        db.close()

async def send_to_integration(integration: Integration, event_type: str, data: dict, db: Session):
    print(f"[Integration] Sending event '{event_type}' to integration {integration.id} of type {integration.integrationType}", flush=True)
    try:
        if integration.integrationType == 'email':
            config = integration.config
            if config.get('email'):
                subject = f"ProjectFlow: {event_type}"
                body = f"Event occurred: {event_type}\nDetails: {json.dumps(data, indent=2)}"
                print(f"[Integration] Sending email to {config['email']} with subject '{subject}'", flush=True)
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
            config['chat_id'] = '1854275407'
            print(f"[Integration] Telegram integration config: {config}", flush=True)
            if config.get('chat_id'):
                message = f"🔔 *{event_type}*\n\n{json.dumps(data, indent=2)}"
                print(f"[Integration] Sending telegram message to chat_id {config['chat_id']}", flush=True)
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
        print(f"[Integration] Failed to send to integration {integration.id}: {e}", flush=True)
        log = WebhookLog(
            integrationId=integration.id,
            eventType=event_type,
            payload=data,
            status='failed',
            errorMessage=str(e)
        )
        db.add(log)
        db.commit()
