from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class UserProfileRequest(BaseModel):
    # --- Biometrics ---
    user_id: str
    age: int
    weight: float
    height: float
    gender: Literal["Male", "Female", "Other"]
    
    # --- Time Constraints ---
    days_per_week: int = Field(..., ge=1, le=7)
    session_duration_minutes: int = Field(..., ge=15)
    
    # --- Preferences & Environment ---
    target_zone: List[str]        # e.g., ["Upper", "Lower"]
    location: Literal["Home", "Gym", "Park"]
    equipment: List[str]          # e.g., ["Dumbbell", "Bench"]
    
    # --- Program Strategy (Crucial for the Agent) ---
    split_type: Literal["Monofrequency", "Multifrequency"]
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]
    
    # --- Constraints & Goals ---
    injuries: List[str]           # e.g., ["knee_pain"]
    goals: List[str]              # e.g., ["Hypertrophy"]

class WorkoutPlanResponse(BaseModel):
    status: str
    plan_id: str
    message: str
    workout_plan: str