from sqlalchemy import Column, Integer, String, Text, ARRAY, Boolean
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Exercise(Base):
    __tablename__ = "exercises"

    # Standard Data
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)           # e.g., "Bench Press"
    muscle_group = Column(String, nullable=False)   # e.g., "Chest"
    equipment = Column(String, nullable=False)      # e.g., "Barbell"
    difficulty = Column(String, nullable=False)     # e.g., "Intermediate"
    
    # Detailed text for the AI to read
    instructions = Column(Text, nullable=False)     
    
    # Safety constraints (Critical for medical logic)
    contraindications = Column(ARRAY(String))       # e.g., ["shoulder_injury", "wrist_pain"]
    
    # The "Brain" of the RAG system
    # 1536 is the standard size for OpenAI embeddings
    embedding = Column(Vector(1536)) 

class UserProfile(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    age = Column(Integer)
    injuries = Column(ARRAY(String))                # e.g., ["lower_back_pain"]
    equipment_available = Column(ARRAY(String))     # e.g., ["dumbbells", "bench"]