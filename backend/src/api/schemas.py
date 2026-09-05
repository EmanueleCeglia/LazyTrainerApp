from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# NOTE ON `user_id`:
# Every request below still accepts a `user_id` so older app builds keep working,
# but the server ALWAYS derives the real owner from the JWT and ignores this field.

class UserProfileRequest(BaseModel):
    # --- Biometrics ---
    user_id: Optional[str] = None  # ignored - see note above
    age: int = Field(..., ge=10, le=100)
    weight: float = Field(..., gt=0, le=500)
    height: float = Field(..., gt=0, le=280)
    gender: Literal["Male", "Female", "Other"]
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]

    # --- Logistics ---
    days_per_week: int = Field(..., ge=1, le=7)
    session_duration_minutes: int = Field(..., ge=15, le=240)

    # --- Environment ---
    location: Literal["Home", "Gym", "Park"]
    equipment: List[str] = []

    # --- Goals ---
    goals: List[str] = Field(..., min_length=1)

class WorkoutPlanResponse(BaseModel):
    status: str
    plan_id: str
    message: str
    workout_plan: str

class PlanSummary(BaseModel):
    """One row in GET /plans."""
    plan_id: str
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None

class PlanDetail(PlanSummary):
    """GET /plans/{id} - the summary plus the full schedule as a JSON string."""
    workout_plan: str

class ExerciseSwapRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    plan_id: Optional[str] = None  # the path parameter is authoritative
    current_exercise_name: str
    day_name: str

    # 1. Specific Request (Highest Priority)
    target_exercise_name: Optional[str] = None

    # 2. Functional Overrides (The "What" and "How")
    new_target_zone: Optional[Literal["Upper", "Lower", "Core", "Full Body", "Cardio"]] = None

    # Force Type Override
    new_force_type: Optional[Literal["Push", "Pull", "Hinge", "Static", "Lunge", "Dynamic", "Squat"]] = None

    # 3. Style/Equipment Preference
    swap_preference: Optional[Literal["Bodyweight Only", "Machine", "Free Weight"]] = None

class DifficultyModificationRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    day_name: str
    target_exercise_names: List[str] = []
    modification_type: str
    new_method: Optional[str] = None
    user_feedback: Optional[str] = None

class ProgressionRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    previous_plan_id: str
    user_feedback: str
    new_goal: Optional[List[str]] = None
    new_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    new_location: Optional[Literal["Home", "Gym", "Park"]] = None

class RestructureRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    new_split_name: str  # e.g., "Full Body", "Push/Pull/Legs", "Upper/Lower"

class BulkSwapExerciseItem(BaseModel):
    day_name: str       # e.g., "Day 1"
    exercise_name: str  # e.g., "Bench Press"

class BulkSwapRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    exercises: List[BulkSwapExerciseItem] = Field(..., min_length=1)

class EquipmentAlternativesRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    day_name: str
    exercise_name: str

class SmartSwapRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    day_name: str
    exercise_name: str
    target_zone: Literal["Upper", "Lower", "Core"]

class ApplyEquipmentSwapRequest(BaseModel):
    user_id: Optional[str] = None  # ignored
    day_name: str
    exercise_name: str
    new_exercise_name: str
