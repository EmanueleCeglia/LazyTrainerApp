import uuid
import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.api.schemas import UserProfileRequest, WorkoutPlanResponse
from src.crew.main import WorkoutCrew
from src.database.connection import get_db
from src.database.models import WorkoutPlan

router = APIRouter()

# --- 1. DEFINE BASE KITS ---
LOCATION_EQUIPMENT = {
    "Gym": [
        "Barbell", "Bench", "Cable Machine", "Dumbbells", "Incline Bench", 
        "Leg Curl Machine", "Leg Extension Machine", "Leg Press Machine", 
        "Machine", "Pull-up Bar", "Rack", "Dip Station", "Parallel Bars"
    ],
    "Park": [
        "Pull-up Bar", "Parallel Bars", "Dip Station", "Bar" 
    ],
    "Home": [] 
}

def clean_json_string(raw_string: str) -> dict:
    """
    Helper to strip Markdown code blocks (```json ... ```) if the LLM adds them.
    """
    try:
        # Remove ```json and ``` identifiers
        clean_str = re.sub(r"```json|```", "", raw_string).strip()
        return json.loads(clean_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON PARSING ERROR: {e}")
        print(f"   Raw Content: {raw_string}")
        # Fallback: Return a partial object so the app doesn't crash
        return {"error": "Failed to parse AI response", "raw_content": raw_string}

@router.get("/")
def health_check():
    return {"status": "running", "message": "LazyTrainer Brain is Active 🧠"}

@router.post("/generate", response_model=WorkoutPlanResponse)
def generate_workout(request: UserProfileRequest, db: Session = Depends(get_db)):
    try:
        # --- 2. MERGE EQUIPMENT ---
        base_kit = LOCATION_EQUIPMENT.get(request.location, [])
        combined_equipment = list(set(base_kit + request.equipment))
        
        user_data = request.model_dump()
        user_data['equipment'] = combined_equipment

        print(f"\n🚀 STARTING CREW for User: {request.user_id}")
        
        # --- 3. RUN AGENTS ---
        workout_crew = WorkoutCrew(user_profile=user_data)
        result_raw = workout_crew.run() # This returns a String

        # --- 4. PARSE & SAVE ---
        # Convert string output to real JSON
        plan_json = clean_json_string(str(result_raw))
        
        # Generate a unique ID for this plan
        plan_id = str(uuid.uuid4())
        
        # Create the DB Entry
        new_plan = WorkoutPlan(
            id=plan_id,
            user_id=request.user_id,
            name=plan_json.get("plan_name", "AI Generated Plan"),
            status="Active",
            schedule=plan_json # Saving the JSON structure directly to JSONB column
        )
        
        db.add(new_plan)
        db.commit()
        print(f"💾 PLAN SAVED! ID: {plan_id}")

        return {
            "status": "success",
            "plan_id": plan_id,
            "message": "Workout generated and saved successfully.",
            "workout_plan": json.dumps(plan_json) # Return stringified JSON for the schema
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))