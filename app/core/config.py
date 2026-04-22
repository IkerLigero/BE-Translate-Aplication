# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "CarbonAltDelete"
    
    # --- SECURITY ---
    # Pydantic will look for this key in your .env file
    REGISTRATION_SECRET: str 
    
    # --- JWT / AUTH ---
    # Add your existing keys here so 'settings' has them
    SECRET_KEY: str = "secret" 
    ALGORITHM: str = "HS256"

    # This replaces the old 'class Config' in Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # This prevents errors if you have extra variables in .env
    )

settings = Settings()