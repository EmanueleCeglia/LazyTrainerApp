from sqlalchemy import Column, Integer, String, Text, ARRAY, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    age = Column(Integer)
    gender = Column(String)
    weight = Column(Float)
    height = Column(Float)
    # --- NEW COLUMN ---
    location = Column(String)  # e.g., "Gym", "Home", "Park"
    experience_level = Column(String) # Beginner, Intermediate, Advanced
    
    equipment_available = Column(ARRAY(String))
    goals = Column(ARRAY(String))

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Always the owner's username, set server-side from the JWT. Never trust a client-supplied value.
    user_id = Column(String, index=True)
    
    name = Column(String)
    description = Column(Text, nullable=True)
    
    status = Column(String, default="Active") 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    schedule = Column(JSONB, nullable=False)