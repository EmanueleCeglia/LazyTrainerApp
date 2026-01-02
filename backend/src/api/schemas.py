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
    
    # NEW: Preference for exercise style (even in Gym)
    exercise_preference: Literal["Mixed", "Bodyweight Only", "Weighted Preferred"] = "Mixed"
    
    # --- Program Strategy ---
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

class ExerciseSwapRequest(BaseModel):
    user_id: str
    plan_id: str
    current_exercise_name: str 
    day_name: str 
    
    # 1. Specific Request (Highest Priority)
    target_exercise_name: Optional[str] = None 
    
    # 2. Functional Overrides (The "What" and "How")
    new_target_zone: Optional[Literal["Upper", "Lower", "Core", "Full Body", "Cardio"]] = None
    
    # NEW: Force Type Override
    new_force_type: Optional[Literal["Push", "Pull", "Hinge", "Static", "Lunge", "Dynamic", "Squat"]] = None
    
    # 3. Style/Equipment Preference
    swap_preference: Optional[Literal["Bodyweight Only", "Machine", "Free Weight"]] = None
    
    injuries: List[str] = []

class DifficultyModificationRequest(BaseModel):
    user_id: str
    day_name: str  
    target_exercise_names: List[str] = [] 
    modification_type: str 
    new_method: Optional[str] = None 
    user_feedback: Optional[str] = None

class ProgressionRequest(BaseModel):
    user_id: str
    previous_plan_id: str
    user_feedback: str
    new_goal: Optional[List[str]] = None
    new_days_per_week: Optional[int] = None
    new_location: Optional[str] = None