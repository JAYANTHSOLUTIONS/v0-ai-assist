"""Pydantic models for request/response validation."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class IntentType(str, Enum):
    SEARCH_FLIGHT = "search_flight"
    SEARCH_HOTEL = "search_hotel"
    BOOK_TRIP = "book_trip"
    GENERAL_INQUIRY = "general_inquiry"
    GREETING = "greeting"

class TravelRequest(BaseModel):
    """Base model for travel-related requests."""
    message: str
    session_id: str
    user_id: Optional[str] = None

class FlightSearchRequest(BaseModel):
    """Model for flight search requests."""
    origin: str = Field(..., description="Departure city or airport code")
    destination: str = Field(..., description="Arrival city or airport code")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Return date for round trip")
    passengers: int = Field(1, ge=1, le=9, description="Number of passengers")
    class_type: str = Field("economy", description="Flight class (economy, business, first)")

class HotelSearchRequest(BaseModel):
    """Model for hotel search requests."""
    location: str = Field(..., description="Hotel location (city or address)")
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(1, ge=1, le=10, description="Number of guests")
    rooms: int = Field(1, ge=1, le=5, description="Number of rooms")

class BookingRequest(BaseModel):
    """Model for booking requests."""
    booking_type: str = Field(..., description="Type of booking (flight, hotel, package)")
    booking_id: str = Field(..., description="ID of the item to book")
    passenger_details: Optional[Dict[str, Any]] = None
    payment_info: Optional[Dict[str, Any]] = None

class ExtractedEntities(BaseModel):
    """Model for entities extracted from user input."""
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    
class FlightResult(BaseModel):
    """Model for flight search results."""
    flight_id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    price: float
    currency: str = "USD"
    available_seats: int

class HotelResult(BaseModel):
    """Model for hotel search results."""
    hotel_id: str
    name: str
    location: str
    rating: float = Field(..., ge=0.0, le=5.0)
    price_per_night: float
    currency: str = "USD"
    amenities: List[str] = Field(default_factory=list)
    available_rooms: int

class BookingResult(BaseModel):
    """Model for booking confirmation."""
    booking_id: str
    booking_type: str
    status: str
    confirmation_number: str
    total_price: float
    currency: str = "USD"
    booking_details: Dict[str, Any]

class UIElement(BaseModel):
    """Model for dynamic UI elements in responses."""
    type: str = Field(..., description="Type of UI element (button, link, card)")
    text: str = Field(..., description="Display text")
    action: str = Field(..., description="Action to perform")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class AssistantResponse(BaseModel):
    """Model for AI assistant responses."""
    message: str
    intent: Optional[IntentType] = None
    entities: Optional[Dict[str, Any]] = None
    results: Optional[List[Union[FlightResult, HotelResult, BookingResult]]] = None
    ui_elements: Optional[List[UIElement]] = None
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class ConversationContext(BaseModel):
    """Model for conversation context."""
    session_id: str
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    current_search: Optional[Dict[str, Any]] = None
    booking_in_progress: Optional[Dict[str, Any]] = None
    last_intent: Optional[IntentType] = None

class ConversationHistory(BaseModel):
    """Model for storing conversation history."""
    session_id: str
    messages: List[AssistantResponse]
