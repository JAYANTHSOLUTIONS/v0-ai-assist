"""Configuration settings for the travel assistant."""
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./travel_assistant.db"

    # Add TripXplo email/password to settings
    tripxplo_email: str
    tripxplo_password: str


    # OpenRouter + DeepSeek API Configuration
    DEEPSEEK_API_KEY: Optional[str] = None  # Will be loaded from .env.local
    DEEPSEEK_BASE_URL: str = "https://openrouter.ai/api/v1"  # Use OpenRouter endpoint
    DEEPSEEK_MODEL: str = "deepseek/deepseek-chat-v3-0324"  # DeepSeek model hosted on OpenRouter

    # External APIs (Mock endpoints)
    FLIGHT_API_URL: str = "http://localhost:8001/api/flights"
    HOTEL_API_URL: str = "http://localhost:8001/api/hotels"
    BOOKING_API_URL: str = "http://localhost:8001/api/bookings"

    # Conversation Settings
    MAX_CONVERSATION_HISTORY: int = 10
    SESSION_TIMEOUT_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "travel_assistant.log"

    class Config:
        env_file = ".env.local"  # <-- your env file name here

settings = Settings()
