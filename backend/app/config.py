from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # GitHub App
    GITHUB_APP_ID: int = os.getenv("GITHUB_APP_ID")
    GITHUB_PRIVATE_KEY_PATH: str = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()