from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://analytics_user:analytics_password@postgres_analytics:5432/analytics_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    AUTH_SERVICE_URL: str = "http://auth:8000"
    
    class Config:
        env_file = ".env"

settings = Settings()
