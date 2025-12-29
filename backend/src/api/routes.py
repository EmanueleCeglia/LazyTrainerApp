import uuid
import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.api.schemas import UserProfileRequest, WorkoutPlanResponse
from src.crew.main import WorkoutCrew
from src.database.connection import get_db
from src.database.models import WorkoutPlan
from src.crew.modifier import WorkoutModifier 
from src.api.schemas import ExerciseSwapRequest
from src.api.schemas import DifficultyModificationRequest
from src.api.schemas import ProgressionRequest

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
    

@router.put("/plans/{plan_id}/swap")
def swap_exercise(plan_id: str, request: ExerciseSwapRequest, db: Session = Depends(get_db)):
    # 1. Fetch Plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    print(f"🔄 SWAPPING: {request.current_exercise_name} on {request.day_name}")

    # 2. Run AI
    try:
        modifier = WorkoutModifier(request)
        result_raw = modifier.find_substitute()
        new_exercise_json = clean_json_string(str(result_raw))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Critical Error: {str(e)}")

    # 🛑 GUARD CLAUSE (The Fix)
    if not new_exercise_json or "error" in new_exercise_json or not new_exercise_json.get("name"):
        print(f"❌ SWAP FAILED. AI Output: {new_exercise_json}")
        raise HTTPException(
            status_code=400, 
            detail=f"Could not find a valid substitute for {request.current_exercise_name}. AI Response: {new_exercise_json.get('raw_content', 'Invalid JSON')}"
        )

    # 3. Update Logic (Only proceeds if we have a valid name)
    current_schedule = dict(plan.schedule)
    day_found = False
    
    for week_key, week_data in current_schedule.items():
        if request.day_name in week_data:
            day_data = week_data[request.day_name]
            exercises = day_data.get("exercises", [])
            
            for i, ex in enumerate(exercises):
                if ex.get("name") == request.current_exercise_name:
                    # Merge Old Data with New Data
                    merged_exercise = {
                        "name": new_exercise_json.get("name"), # Guaranteed not null now
                        "sets": new_exercise_json.get("sets", ex.get("sets")),
                        "reps": new_exercise_json.get("reps", ex.get("reps")),
                        "rest": new_exercise_json.get("rest", ex.get("rest")),
                        "notes": new_exercise_json.get("notes", f"Swapped from {request.current_exercise_name}")
                    }
                    
                    exercises[i] = merged_exercise
                    day_found = True
                    break
        if day_found: break

    if not day_found:
        raise HTTPException(status_code=404, detail=f"Exercise '{request.current_exercise_name}' not found in {request.day_name}")

    # 4. Save
    plan.schedule = current_schedule
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(plan, "schedule") 
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Swapped {request.current_exercise_name} for {new_exercise_json.get('name')}",
        "new_exercise": merged_exercise
    }

@router.put("/plans/{plan_id}/adjust")
def adjust_difficulty(plan_id: str, request: DifficultyModificationRequest, db: Session = Depends(get_db)):
    # 1. Fetch Plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    print(f"🎛️ ADJUSTING: {request.modification_type} for {request.day_name}")

    # 2. Extract the Target Exercises
    current_schedule = dict(plan.schedule)
    exercises_to_modify = []
    
    # Helper to find the day data
    day_data = None
    for week in current_schedule.values():
        if request.day_name in week:
            day_data = week[request.day_name]
            break
            
    if not day_data:
        raise HTTPException(status_code=404, detail=f"{request.day_name} not found in plan")

    all_exercises = day_data.get("exercises", [])
    
    # Filter: If target_names provided, select only those. Else, select ALL.
    if request.target_exercise_names:
        exercises_to_modify = [ex for ex in all_exercises if ex['name'] in request.target_exercise_names]
    else:
        exercises_to_modify = all_exercises

    if not exercises_to_modify:
        raise HTTPException(status_code=404, detail="No matching exercises found to modify")

    # 3. Run AI Modifier
    try:
        modifier = WorkoutModifier(request)
        # Pass ONLY the specific exercises we want to change
        result_raw = modifier.adjust_difficulty(exercises_to_modify)
        modified_list = clean_json_string(str(result_raw))
        
        # Validation: Ensure we got a list back
        if isinstance(modified_list, dict): 
            # Sometimes LLM wraps list in {"exercises": [...]}
            modified_list = modified_list.get("exercises", [modified_list])
        if not isinstance(modified_list, list):
            modified_list = [modified_list]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

    # 4. Merge Back (The Surgery)
    # We iterate through the original list and swap in the modified versions
    updated_count = 0
    for new_ex in modified_list:
        for i, old_ex in enumerate(all_exercises):
            if old_ex["name"] == new_ex["name"]:
                all_exercises[i] = new_ex # Replace with new parameters
                updated_count += 1
    
    # 5. Save
    plan.schedule = current_schedule
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(plan, "schedule") 
    db.commit()

    return {
        "status": "success",
        "message": f"Updated {updated_count} exercises.",
        "modified_exercises": modified_list
    }

@router.post("/generate/next", response_model=WorkoutPlanResponse)
def generate_next_block(request: ProgressionRequest, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Previous Plan
        old_plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == request.previous_plan_id).first()
        if not old_plan:
            raise HTTPException(status_code=404, detail="Previous plan not found")

        # 2. Re-construct User Profile
        # We need the user's stats. In a real app, you'd fetch this from a User table.
        # For now, we will try to infer context or require a User Profile lookup.
        # Let's assume we can get basic stats from the User table using user_id.
        # (Assuming you have a User model, otherwise we might need to pass stats in request)
        
        # simplified: We will carry over defaults from the previous plan if stored, 
        # or realistically, you might want to pass the full profile again.
        # To keep it simple, let's assume we use standard defaults + the history.
        
        # Ideally, fetch this from DB:
        user_profile_data = {
            "user_id": request.user_id,
            "days_per_week": request.new_days_per_week or 4, # Fallback or Override
            "location": request.new_location or "Gym",
            "goals": request.new_goal or ["Hypertrophy"],
            "equipment": [], # Will be filled by merge logic below
            "split_type": "Multifrequency", # Default or fetch from user pref
            "experience_level": "Intermediate",
            "injuries": [],
            "target_zone": ["Full Body"]
        }

        # 3. Inject History
        # We pass a summary of the schedule to the Agent
        user_profile_data['previous_plan'] = str(old_plan.schedule) 
        user_profile_data['feedback'] = request.user_feedback

        # 4. Merge Equipment (Same logic as /generate)
        base_kit = LOCATION_EQUIPMENT.get(user_profile_data['location'], [])
        user_profile_data['equipment'] = base_kit # Add user extras if you track them

        print(f"📈 GENERATING PROGRESSION for User: {request.user_id}")
        print(f"   Feedback: {request.user_feedback}")

        # 5. Run the Crew
        workout_crew = WorkoutCrew(user_profile=user_profile_data)
        result_raw = workout_crew.run()
        plan_json = clean_json_string(str(result_raw))

        # 6. Save New Plan
        new_plan_id = str(uuid.uuid4())
        new_plan = WorkoutPlan(
            id=new_plan_id,
            user_id=request.user_id,
            name=plan_json.get("plan_name", "Progression Block"),
            status="Active",
            schedule=plan_json
        )
        
        # Archive the old plan? (Optional)
        # old_plan.status = "Completed"
        
        db.add(new_plan)
        db.commit()

        return {
            "status": "success",
            "plan_id": new_plan_id,
            "message": "Progression generated successfully.",
            "workout_plan": json.dumps(plan_json)
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))