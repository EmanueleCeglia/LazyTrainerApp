from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class UserProfileRequest(BaseModel):
    # --- Biometrics ---
    user_id: str
    age: int
    weight: float # kg
    height: float # cm
    gender: Literal["Male", "Female", "Other"]
    
    # --- Logistics ---
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]
    goals: List[str] = Field(..., example=["Hypertrophy", "Strength"])
    
    # --- Constraints (Crucial for the Logic) ---
    equipment: List[str] = Field(..., example=["Dumbbell", "Barbell", "Bench"])
    injuries: List[str] = Field(default=[], example=["knee_pain", "lower_back"])
    
    # --- Schedule ---
    days_per_week: int = Field(3, ge=1, le=7)
    session_duration_minutes: int = Field(60, ge=15)

class WorkoutPlanResponse(BaseModel):
    status: str
    plan_id: str
    message: str
    workout_plan: str  # <--- NEW FIELD: This will hold the actual AI output