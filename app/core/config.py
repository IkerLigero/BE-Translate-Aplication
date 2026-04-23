# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

# This file centralizes all configuration settings for the application, including secrets and environment variables.

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

    # Environment variables
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # This prevents errors if you have extra variables in .env
    )

settings = Settings()