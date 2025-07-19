"""Database models and setup for conversation persistence."""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import json

from config import settings

# SQLAlchemy setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ConversationMessage(Base):
    """Database model for storing conversation messages."""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    message_type = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSON, nullable=True)  # Renamed to avoid conflict
    timestamp = Column(DateTime, default=datetime.utcnow)

class ConversationSession(Base):
    """Database model for tracking conversation sessions."""
    __tablename__ = "conversation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON, nullable=True)  # Store session context

# Pydantic models for API
class MessageCreate(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: int
    session_id: str
    user_id: Optional[str]
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

class ConversationHistory(BaseModel):
    session_id: str
    messages: List[MessageResponse]
    total_messages: int

# Database operations
class DatabaseManager:
    """Handles all database operations for conversations."""
    
    def __init__(self):
        Base.metadata.create_all(bind=engine)
    
    def get_db(self) -> Session:
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            pass
    
    def create_message(self, db: Session, message: MessageCreate) -> ConversationMessage:
        """Create a new conversation message."""
        db_message = ConversationMessage(
            session_id=message.session_id,
            user_id=message.user_id,
            message_type=message.message_type,
            content=message.content,
            extra_metadata=message.metadata  # Note the rename here
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    
    def get_conversation_history(
        self, 
        db: Session, 
        session_id: str, 
        limit: int = None
    ) -> List[ConversationMessage]:
        """Retrieve conversation history for a session."""
        query = db.query(ConversationMessage).filter(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.timestamp.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def create_or_update_session(
        self, 
        db: Session, 
        session_id: str, 
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """Create or update a conversation session."""
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id
        ).first()
        
        if session:
            session.last_activity = datetime.utcnow()
            if context:
                session.context = context
        else:
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                context=context
            )
            db.add(session)
        
        db.commit()
        db.refresh(session)
        return session
    
    def cleanup_old_sessions(self, db: Session, hours: int = 24):
        """Clean up old inactive sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Delete old messages
        db.query(ConversationMessage).filter(
            ConversationMessage.timestamp < cutoff_time
        ).delete()
        
        # Delete old sessions
        db.query(ConversationSession).filter(
            ConversationSession.last_activity < cutoff_time
        ).delete()
        
        db.commit()

# Global database manager instance
db_manager = DatabaseManager()
