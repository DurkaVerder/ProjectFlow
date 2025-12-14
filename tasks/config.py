from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    AUTH_SERVICE_URL: str = "http://auth:8000"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"

    class Config:
        env_file = ".env"


settings = Settings()
