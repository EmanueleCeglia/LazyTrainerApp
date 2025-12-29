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

class ExerciseSwapRequest(BaseModel):
    user_id: str
    target_muscle_group: str # e.g. "Legs" or "Chest" (Optional context)
    current_exercise_name: str # The one we want to remove
    day_name: str # e.g. "Day 1"
    available_equipment: List[str] # Current equipment list
    injuries: List[str] = []

class DifficultyModificationRequest(BaseModel):
    user_id: str
    day_name: str  # e.g., "Day 1"
    target_exercise_names: List[str] = []  # If empty, applies to the WHOLE day
    
    # "scaling" (Adjust sets/reps/weight) or "method" (Change style like EMOM, Supersets)
    modification_type: str 
    
    # Optional parameters
    new_method: Optional[str] = None     # e.g. "5x5", "EMOM", "Pyramid" (If null, AI picks)
    user_feedback: Optional[str] = None  # e.g. "Too easy", "I have only 30 mins", "My knees hurt"

class ProgressionRequest(BaseModel):
    user_id: str
    previous_plan_id: str
    user_feedback: str  # e.g., "Ready for more volume", "Knees hurt", "Switching to strength"
    
    # Optional overrides (if they want to change location/days for the NEW block)
    new_goal: Optional[List[str]] = None
    new_days_per_week: Optional[int] = None
    new_location: Optional[str] = None