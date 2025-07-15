from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # GitHub App
    GITHUB_APP_ID: int
    GITHUB_PRIVATE_KEY_PATH: str = "mycodereviewbot.2025-07-01.private-key.pem"
    GITHUB_WEBHOOK_SECRET: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()