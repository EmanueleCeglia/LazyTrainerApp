from sqlalchemy import Column, Integer, String, Text, ARRAY, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB  # <--- Added for WorkoutPlan
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- Identification ---
    name = Column(String, unique=True, nullable=False)
    
    # --- Biomechanics (The "Brain" of the schema) ---
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
    injuries = Column(ARRAY(String))
    equipment_available = Column(ARRAY(String))
    goals = Column(ARRAY(String))

# --- NEW TABLE: THE MEMORY ---
class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    # We use UUID (String) for the Plan ID so it's easy to share/reference in API calls
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # We store user_id as String because it often comes from external Auth (Firebase/Auth0)
    # If you strictly link to UserProfile.id, we can change this to Integer later.
    user_id = Column(String, index=True) 
    
    # Metadata
    name = Column(String) # e.g. "Hypertrophy Week 1"
    description = Column(Text, nullable=True)
    
    # State: Active (Current), Completed (Done), Archived (Deleted/Old)
    status = Column(String, default="Active") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # THE CORE: Stores the full tree (Days -> Exercises -> Sets/Reps)
    # This allows us to modify specific parts without inflexible SQL relations
    schedule = Column(JSONB, nullable=False)