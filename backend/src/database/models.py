from sqlalchemy import Column, Integer, String, Text, ARRAY, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Identification ---
    name = Column(String, unique=True, nullable=False)
    
    # --- Biomechanics ---
    target_zone = Column(String, nullable=False)
    force_type = Column(String, nullable=True)
    muscle_group = Column(String, nullable=False)
    secondary_muscles = Column(ARRAY(String))
    mechanics = Column(String, nullable=True)
    
    category = Column(String, nullable=False) 
    
    # --- Logistics ---
    equipment = Column(ARRAY(String), nullable=False)
    difficulty = Column(String, nullable=False)
    
    # --- Content ---
    instructions = Column(Text, nullable=False)
    video_url = Column(String, nullable=True)
    
    # --- Safety ---
    contraindications = Column(ARRAY(String))          
    
    # --- RAG ---
    embedding = Column(Vector(1536)) 

class UserProfile(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    age = Column(Integer)
    gender = Column(String)
    weight = Column(Float)
    height = Column(Float)
    experience_level = Column(String)
    
    # --- NEW COLUMN ---
    location = Column(String)  # e.g., "Gym", "Home", "Park"
    
    injuries = Column(ARRAY(String))
    equipment_available = Column(ARRAY(String))
    goals = Column(ARRAY(String))

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True) 
    
    name = Column(String)
    description = Column(Text, nullable=True)
    
    status = Column(String, default="Active") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    schedule = Column(JSONB, nullable=False)