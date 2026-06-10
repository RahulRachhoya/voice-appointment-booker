"""Database models for Voice AI Appointment Booker."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Call(Base):
    """Track incoming calls and their outcomes."""
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True)
    call_sid = Column(String(100), unique=True, index=True)
    caller_number = Column(String(20))
    status = Column(String(20), default="initiated")  # initiated, in_progress, completed, failed
    
    # Conversation state
    turn_count = Column(Integer, default=0)
    intent = Column(String(50))  # book, cancel, reschedule, info
    appointment_date = Column(DateTime, nullable=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    service_type = Column(String(100))
    
    # Outcome
    appointment_booked = Column(Boolean, default=False)
    transcript = Column(Text)  # Full conversation
    summary = Column(Text)
    call_duration = Column(Float)  # seconds
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Appointment(Base):
    """Booked appointments."""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, nullable=True)
    
    # Customer
    customer_name = Column(String(100))
    customer_phone = Column(String(20))
    customer_email = Column(String(100), nullable=True)
    
    # Appointment details
    service_type = Column(String(100))
    appointment_date = Column(DateTime)
    duration_minutes = Column(Integer, default=30)
    notes = Column(Text)
    
    # Sync status
    google_event_id = Column(String(100), nullable=True)
    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, confirmed, cancelled, completed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationTurn(Base):
    """Individual conversation turns for analytics."""
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, index=True)
    
    turn_number = Column(Integer)
    role = Column(String(10))  # user, assistant
    
    # Raw audio (stored as path to file)
    audio_path = Column(String(200), nullable=True)
    
    # Transcribed/Generated text
    text = Column(Text)
    
    # Intent extracted from this turn
    intent = Column(String(50), nullable=True)
    entities = Column(Text)  # JSON of extracted entities
    
    # Timing
    latency_ms = Column(Integer)  # Time to generate response
    
    created_at = Column(DateTime, default=datetime.utcnow)