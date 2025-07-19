"""FastAPI route handlers for the travel assistant."""
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from loguru import logger

from models import (
    TravelRequest, AssistantResponse, FlightSearchRequest, 
    HotelSearchRequest, BookingRequest, ConversationHistory
)
from database import db_manager
from langgraph_workflow import travel_workflow
from external_apis import external_apis

import tripxplo  # <-- Import TripXplo client

# Create API router
router = APIRouter()

def get_db():
    """Dependency to get database session."""
    db = db_manager.get_db()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat", response_model=AssistantResponse)
async def chat_with_assistant(request: TravelRequest):
    """Main chat endpoint for interacting with the travel assistant."""
    logger.info(f"Chat request from session: {request.session_id}")
    
    try:
        # Run the LangGraph workflow
        response = await travel_workflow.run_workflow(
            user_input=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/search-flight")
async def search_flights(request: FlightSearchRequest):
    """Direct flight search endpoint."""
    logger.info(f"Flight search: {request.origin} -> {request.destination}")
    
    try:
        flights = await external_apis.search_flights(request)
        return {
            "flights": flights,
            "total_results": len(flights),
            "search_params": request.dict()
        }
        
    except Exception as e:
        logger.error(f"Flight search error: {e}")
        raise HTTPException(status_code=500, detail="Flight search failed")

@router.post("/search-hotel")
async def search_hotels(request: HotelSearchRequest):
    """Direct hotel search endpoint."""
    logger.info(f"Hotel search in: {request.location}")
    
    try:
        hotels = await external_apis.search_hotels(request)
        return {
            "hotels": hotels,
            "total_results": len(hotels),
            "search_params": request.dict()
        }
        
    except Exception as e:
        logger.error(f"Hotel search error: {e}")
        raise HTTPException(status_code=500, detail="Hotel search failed")

@router.post("/book-trip")
async def book_trip(request: BookingRequest):
    """Direct booking endpoint."""
    logger.info(f"Booking request: {request.booking_type} - {request.booking_id}")
    
    try:
        booking = await external_apis.create_booking(
            request.booking_type,
            request.booking_id,
            request.dict()
        )
        
        return {
            "booking": booking,
            "status": "success",
            "message": f"Your {request.booking_type} has been booked successfully!"
        }
        
    except Exception as e:
        logger.error(f"Booking error: {e}")
        raise HTTPException(status_code=500, detail="Booking failed")

@router.get("/conversation/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str, 
    limit: Optional[int] = 50,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session."""
    logger.info(f"Retrieving conversation history for session: {session_id}")
    
    try:
        messages = db_manager.get_conversation_history(db, session_id, limit)
        
        message_responses = []
        for msg in reversed(messages):  # Chronological order
            message_responses.append({
                "id": msg.id,
                "session_id": msg.session_id,
                "user_id": msg.user_id,
                "message_type": msg.message_type,
                "content": msg.content,
                "metadata": msg.metadata,
                "timestamp": msg.timestamp
            })
        
        return ConversationHistory(
            session_id=session_id,
            messages=message_responses,
            total_messages=len(message_responses)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")

@router.delete("/conversation/{session_id}")
async def clear_conversation(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Clear conversation history for a session."""
    logger.info(f"Clearing conversation for session: {session_id}")
    
    try:
        # Delete messages for the session
        deleted_count = db.query(db_manager.ConversationMessage).filter(
            db_manager.ConversationMessage.session_id == session_id
        ).delete()
        
        # Delete session
        db.query(db_manager.ConversationSession).filter(
            db_manager.ConversationSession.session_id == session_id
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Cleared {deleted_count} messages for session {session_id}",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

@router.get("/sessions")
async def list_active_sessions(db: Session = Depends(get_db)):
    """List all active conversation sessions."""
    try:
        sessions = db.query(db_manager.ConversationSession).order_by(
            db_manager.ConversationSession.last_activity.desc()
        ).limit(100).all()
        
        session_list = []
        for session in sessions:
            # Get message count for each session
            message_count = db.query(db_manager.ConversationMessage).filter(
                db_manager.ConversationMessage.session_id == session.session_id
            ).count()
            
            session_list.append({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "message_count": message_count,
                "context": session.context
            })
        
        return {
            "sessions": session_list,
            "total_sessions": len(session_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")

@router.post("/session/new")
async def create_new_session(user_id: Optional[str] = None):
    """Create a new conversation session."""
    session_id = str(uuid.uuid4())
    
    try:
        db = db_manager.get_db()
        db_manager.create_or_update_session(db, session_id, user_id)
        db.close()
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "AI Travel Assistant",
        "version": "1.0.0"
    }

# Background task for cleanup
async def cleanup_old_sessions():
    """Background task to clean up old sessions."""
    try:
        db = db_manager.get_db()
        db_manager.cleanup_old_sessions(db, hours=24)
        db.close()
        logger.info("Completed session cleanup")
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")

@router.post("/admin/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Manually trigger session cleanup."""
    background_tasks.add_task(cleanup_old_sessions)
    return {"message": "Cleanup task scheduled", "status": "success"}

### === TripXplo API Integration === ###

@router.get("/tripxplo/packages")
async def list_packages(search: Optional[str] = "", limit: int = 100, offset: int = 0):
    try:
        packages = tripxplo.get_packages(search=search, limit=limit, offset=offset)
        return {"packages": packages}
    except Exception as e:
        logger.error(f"Error in /tripxplo/packages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch packages")

@router.get("/tripxplo/package/{package_id}")
async def package_details(package_id: str):
    try:
        details = tripxplo.get_package_details(package_id)
        return {"details": details}
    except Exception as e:
        logger.error(f"Error in /tripxplo/package/{package_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch package details")

@router.post("/tripxplo/package/{package_id}/pricing")
async def package_pricing(package_id: str, params: dict):
    try:
        pricing = tripxplo.get_package_pricing(package_id, params)
        return {"pricing": pricing}
    except Exception as e:
        logger.error(f"Error in /tripxplo/package/{package_id}/pricing: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch package pricing")

@router.get("/tripxplo/package/{package_id}/hotels")
async def package_hotels(package_id: str):
    try:
        hotels = tripxplo.get_available_hotels(package_id)
        return {"hotels": hotels}
    except Exception as e:
        logger.error(f"Error in /tripxplo/package/{package_id}/hotels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch hotels")

@router.get("/tripxplo/package/{package_id}/vehicles")
async def package_vehicles(package_id: str):
    try:
        vehicles = tripxplo.get_available_vehicles(package_id)
        return {"vehicles": vehicles}
    except Exception as e:
        logger.error(f"Error in /tripxplo/package/{package_id}/vehicles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch vehicles")

@router.get("/tripxplo/package/{package_id}/activities")
async def package_activities(package_id: str):
    try:
        activities = tripxplo.get_available_activities(package_id)
        return {"activities": activities}
    except Exception as e:
        logger.error(f"Error in /tripxplo/package/{package_id}/activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activities")

@router.get("/tripxplo/interests")
async def get_interests():
    try:
        interests = tripxplo.get_interests()
        return {"interests": interests}
    except Exception as e:
        logger.error(f"Error in /tripxplo/interests: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch interests")

@router.get("/tripxplo/destinations/search")
async def search_destinations(search: Optional[str] = ""):
    try:
        destinations = tripxplo.search_destinations(search=search)
        return {"destinations": destinations}
    except Exception as e:
        logger.error(f"Error in /tripxplo/destinations/search: {e}")
        raise HTTPException(status_code=500, detail="Failed to search destinations")
