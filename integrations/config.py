from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://integrations_user:integrations_password@postgres_integrations:5432/integrations_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    AUTH_SERVICE_URL: str = "http://auth:8000"
    
    # Email settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = "8508817832:AAEg2G7SeklAHNk0JVdNfctqR-yJtLoSCbw"
    
    # GitHub settings
    GITHUB_API_URL: str = "https://api.github.com"
    
    class Config:
        env_file = ".env"

settings = Settings()
