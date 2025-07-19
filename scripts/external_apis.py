"""Mock external API clients for flights, hotels, and bookings."""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger

from models import FlightResult, HotelResult, BookingResult, FlightSearchRequest, HotelSearchRequest

class MockExternalAPIs:
    """Mock external APIs for demonstration purposes."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def search_flights(self, request: FlightSearchRequest) -> List[FlightResult]:
        """Mock flight search API."""
        logger.info(f"Searching flights: {request.origin} -> {request.destination}")
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate mock flight results
        airlines = ["American Airlines", "Delta", "United", "Southwest", "JetBlue"]
        flights = []
        
        for i in range(random.randint(3, 8)):
            airline = random.choice(airlines)
            flight_number = f"{airline[:2].upper()}{random.randint(100, 999)}"
            
            # Generate realistic times
            departure_hour = random.randint(6, 22)
            duration_hours = random.randint(2, 8)
            arrival_hour = (departure_hour + duration_hours) % 24
            
            flight = FlightResult(
                flight_id=f"flight_{i+1}_{random.randint(1000, 9999)}",
                airline=airline,
                flight_number=flight_number,
                origin=request.origin,
                destination=request.destination,
                departure_time=f"{departure_hour:02d}:{random.randint(0, 59):02d}",
                arrival_time=f"{arrival_hour:02d}:{random.randint(0, 59):02d}",
                duration=f"{duration_hours}h {random.randint(0, 59)}m",
                price=round(random.uniform(200, 1200), 2),
                available_seats=random.randint(5, 50)
            )
            flights.append(flight)
        
        # Sort by price
        flights.sort(key=lambda x: x.price)
        return flights
    
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelResult]:
        """Mock hotel search API."""
        logger.info(f"Searching hotels in: {request.location}")
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate mock hotel results
        hotel_names = [
            "Grand Plaza Hotel", "Comfort Inn & Suites", "Luxury Resort & Spa",
            "Business Center Hotel", "Boutique Downtown", "Seaside Resort",
            "Mountain View Lodge", "City Center Hotel", "Airport Inn"
        ]
        
        amenities_pool = [
            "Free WiFi", "Pool", "Gym", "Spa", "Restaurant", "Bar",
            "Room Service", "Parking", "Pet Friendly", "Business Center"
        ]
        
        hotels = []
        
        for i in range(random.randint(4, 10)):
            name = random.choice(hotel_names)
            amenities = random.sample(amenities_pool, random.randint(3, 7))
            
            hotel = HotelResult(
                hotel_id=f"hotel_{i+1}_{random.randint(1000, 9999)}",
                name=f"{name} {random.choice(['Downtown', 'Airport', 'Beach', 'Center'])}",
                location=request.location,
                rating=round(random.uniform(3.0, 5.0), 1),
                price_per_night=round(random.uniform(80, 500), 2),
                amenities=amenities,
                available_rooms=random.randint(1, 20)
            )
            hotels.append(hotel)
        
        # Sort by rating (descending)
        hotels.sort(key=lambda x: x.rating, reverse=True)
        return hotels
    
    async def create_booking(
        self, 
        booking_type: str, 
        item_id: str, 
        booking_details: Dict[str, Any]
    ) -> BookingResult:
        """Mock booking creation API."""
        logger.info(f"Creating {booking_type} booking for item: {item_id}")
        
        # Simulate API delay
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # Generate mock booking result
        confirmation_number = f"{booking_type.upper()[:2]}{random.randint(100000, 999999)}"
        
        # Calculate mock price based on booking type
        if booking_type == "flight":
            base_price = random.uniform(200, 1200)
        elif booking_type == "hotel":
            base_price = random.uniform(80, 500)
        else:
            base_price = random.uniform(500, 2000)
        
        booking = BookingResult(
            booking_id=f"booking_{random.randint(10000, 99999)}",
            booking_type=booking_type,
            status="confirmed",
            confirmation_number=confirmation_number,
            total_price=round(base_price, 2),
            booking_details=booking_details
        )
        
        return booking
    
    async def get_flight_details(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed flight information."""
        await asyncio.sleep(0.5)
        
        return {
            "flight_id": flight_id,
            "baggage_policy": "1 carry-on, 1 checked bag included",
            "cancellation_policy": "Free cancellation within 24 hours",
            "seat_map": "Available for selection",
            "meal_service": "Complimentary snacks and beverages"
        }
    
    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed hotel information."""
        await asyncio.sleep(0.5)
        
        return {
            "hotel_id": hotel_id,
            "check_in_time": "3:00 PM",
            "check_out_time": "11:00 AM",
            "cancellation_policy": "Free cancellation up to 24 hours before check-in",
            "policies": ["No smoking", "Pet policy varies", "Valid ID required"],
            "contact": "+1-555-0123"
        }

# Global external APIs instance
external_apis = MockExternalAPIs()
