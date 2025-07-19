"""Test client for the AI Travel Assistant API."""
import asyncio
import httpx
import json
import uuid
from datetime import datetime
from loguru import logger

class TravelAssistantTestClient:
    """Test client for the AI Travel Assistant API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())
