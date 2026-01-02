import uuid
import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.api.schemas import UserProfileRequest, WorkoutPlanResponse
from src.crew.main import WorkoutCrew
from src.database.connection import get_db
from src.database.models import WorkoutPlan, UserProfile
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

        # --- [NEW] SAVE USER CONTEXT TO DB (The "Memory") ---
        # We use 'username' to match 'user_id' from the request
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        
        if not user_profile:
            # Create New Profile
            user_profile = UserProfile(
                username=request.user_id,
                location=request.location, # Now storing Location
                equipment_available=combined_equipment, # Storing the FULL list (Gym + Custom)
                experience_level=request.experience_level,
                goals=request.goals,
                injuries=request.injuries
            )
            db.add(user_profile)
            print(f"🆕 Created profile for {request.user_id}")
        else:
            # Update Existing Profile
            user_profile.location = request.location
            user_profile.equipment_available = combined_equipment
            user_profile.experience_level = request.experience_level
            user_profile.goals = request.goals
            user_profile.injuries = request.injuries
            print(f"♻️ Updated profile for {request.user_id}")
            
        db.commit() # Save immediately

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
            schedule=plan_json 
        )
        
        db.add(new_plan)
        db.commit()
        print(f"💾 PLAN SAVED! ID: {plan_id}")

        return {
            "status": "success",
            "plan_id": plan_id,
            "message": "Workout generated and saved successfully.",
            "workout_plan": json.dumps(plan_json) 
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

    # --- 2. FETCH MEMORY (New Logic) ---
    # We look up the user to see what equipment/location they possess.
    user_profile = db.query(UserProfile).filter(UserProfile.username == plan.user_id).first()
    
    saved_equipment = []
    
    # Priority: 1. Use stored profile equipment (Best) -> 2. Default to Gym (Fallback)
    if user_profile and user_profile.equipment_available:
        saved_equipment = user_profile.equipment_available
        print(f"   🧠 Memory: Found {len(saved_equipment)} items for user.")
    else:
        print("   ⚠️ Memory Warning: User Profile not found or empty. Defaulting to Gym context.")
        saved_equipment = LOCATION_EQUIPMENT["Gym"]

    # --- 3. Run AI with Context ---
    try:
        # We pass BOTH the request and the fetched equipment to the modifier
        modifier = WorkoutModifier(request, saved_equipment) 
        result_raw = modifier.find_substitute()
        new_exercise_json = clean_json_string(str(result_raw))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Critical Error: {str(e)}")

    # 🛑 GUARD CLAUSE
    if not new_exercise_json or "error" in new_exercise_json or not new_exercise_json.get("name"):
        print(f"❌ SWAP FAILED. AI Output: {new_exercise_json}")
        raise HTTPException(
            status_code=400, 
            detail=f"Could not find a valid substitute. AI Response: {new_exercise_json.get('raw_content', 'Invalid JSON')}"
        )

    # 4. Update Logic (Remains the same)
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

    # 5. Save
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
        # Note: adjust_difficulty doesn't use equipment list heavily, but the class init requires it.
        # We pass an empty list as a placeholder since we are only changing numbers, not exercises.
        modifier = WorkoutModifier(request, []) 
        
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

        # 2. Re-construct User Profile from DB (More reliable than re-inferring)
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        
        if not user_profile:
             raise HTTPException(status_code=404, detail="User Profile not found. Cannot generate progression.")

        # Build profile data for the Crew
        user_profile_data = {
            "user_id": request.user_id,
            "days_per_week": request.new_days_per_week or 4,
            "location": request.new_location or user_profile.location, # Use new or stored
            "goals": request.new_goal or user_profile.goals,
            "equipment": user_profile.equipment_available, # Use stored equipment
            "split_type": "Multifrequency", # Default
            "experience_level": user_profile.experience_level,
            "injuries": user_profile.injuries or [],
            "target_zone": ["Full Body"] # Default or fetch
        }
        
        # 3. Inject History
        user_profile_data['previous_plan'] = str(old_plan.schedule) 
        user_profile_data['feedback'] = request.user_feedback

        print(f"📈 GENERATING PROGRESSION for User: {request.user_id}")
        print(f"   Feedback: {request.user_feedback}")

        # 4. Run the Crew
        workout_crew = WorkoutCrew(user_profile=user_profile_data)
        result_raw = workout_crew.run()
        plan_json = clean_json_string(str(result_raw))

        # 5. Save New Plan
        new_plan_id = str(uuid.uuid4())
        new_plan = WorkoutPlan(
            id=new_plan_id,
            user_id=request.user_id,
            name=plan_json.get("plan_name", "Progression Block"),
            status="Active",
            schedule=plan_json
        )
        
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