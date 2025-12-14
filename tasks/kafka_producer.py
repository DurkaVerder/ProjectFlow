import json
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from config import settings

class KafkaProducer:
    def __init__(self):
        self.producer = None
    
    async def start(self):
        max_retries = 30
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.producer.start()
                print(f"Successfully connected to Kafka at {settings.KAFKA_BOOTSTRAP_SERVERS}")
                return
            except KafkaConnectionError:
                if attempt < max_retries - 1:
                    print(f"Kafka connection attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    print("Failed to connect to Kafka after all retries")
                    raise
    
    async def stop(self):
        if self.producer:
            await self.producer.stop()
    
    async def send_event(self, topic: str, event: dict):
        if self.producer:
            await self.producer.send_and_wait(topic, event)

kafka_producer = KafkaProducer()
