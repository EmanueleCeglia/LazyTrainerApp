import uuid
import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.api.schemas import UserProfileRequest, WorkoutPlanResponse
from src.ai.pipeline import WorkoutPipeline, WorkoutModifier, BulkExerciseSwapper
from src.database.connection import get_db
from src.database.models import WorkoutPlan, UserProfile
from src.api.schemas import ExerciseSwapRequest
from src.api.schemas import DifficultyModificationRequest
from src.api.schemas import ProgressionRequest
from src.api.schemas import RestructureRequest
from src.api.schemas import BulkSwapRequest
from src.api.schemas import EquipmentAlternativesRequest, SmartSwapRequest, ApplyEquipmentSwapRequest

router = APIRouter()

# --- 1. DEFINE BASE KITS ---
LOCATION_EQUIPMENT = {
    "Gym": [
        "Machine", "Cable", "Barbell", "Dumbbells", "Bench",
        "Squat Rack", "Smith Machine", "Kettlebell",
        "Pull-up Bar", "Parallel Bars", "Low Bar", "Rings",
        "Bodyweight"
    ],
    "Park": [
        "Pull-up Bar", "Parallel Bars", "Low Bar",
        "Bodyweight"
    ],
    "Home": [
        "Bodyweight"
    ]
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
                goals=request.goals,
                age=request.age,
                gender=request.gender,
                weight=request.weight,
                height=request.height,
                experience_level=request.experience_level
            )
            db.add(user_profile)
            print(f"Created profile for {request.user_id}")
        else:
            # Update Existing Profile
            user_profile.location = request.location
            user_profile.equipment_available = combined_equipment
            user_profile.goals = request.goals
            user_profile.age = request.age
            user_profile.gender = request.gender
            user_profile.weight = request.weight
            user_profile.height = request.height
            user_profile.experience_level = request.experience_level
            print(f"Updated profile for {request.user_id}")
            
        db.commit() # Save immediately

        print(f"\nSTARTING PIPELINE for User: {request.user_id}")
        
        # --- 3. RUN PIPELINE ---
        pipeline = WorkoutPipeline(user_profile=user_data, equipment=combined_equipment)
        plan_json = pipeline.generate_plan()
        
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
        print(f"PLAN SAVED! ID: {plan_id}")

        return {
            "status": "success",
            "plan_id": plan_id,
            "message": "Workout generated and saved successfully.",
            "workout_plan": json.dumps(plan_json) 
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.put("/plans/{plan_id}/swap")
def swap_exercise(plan_id: str, request: ExerciseSwapRequest, db: Session = Depends(get_db)):
    # 1. Fetch Plan
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    print(f"SWAPPING: {request.current_exercise_name} on {request.day_name}")

    # --- 2. FETCH MEMORY (New Logic) ---
    # We look up the user to see what equipment/location they possess.
    user_profile = db.query(UserProfile).filter(UserProfile.username == plan.user_id).first()
    
    saved_equipment = []
    
    # Priority: 1. Use stored profile equipment (Best) -> 2. Default to Gym (Fallback)
    if user_profile and user_profile.equipment_available:
        saved_equipment = user_profile.equipment_available
        print(f"   Memory: Found {len(saved_equipment)} items for user.")
    else:
        print("   Memory Warning: User Profile not found or empty. Defaulting to Gym context.")
        saved_equipment = LOCATION_EQUIPMENT["Gym"]

    # --- 3. Run AI with Context ---
    try:
        # We pass BOTH the request and the fetched equipment to the modifier
        modifier = WorkoutModifier(request, saved_equipment) 
        new_exercise_json = modifier.find_substitute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Critical Error: {str(e)}")

    # 🛑 GUARD CLAUSE
    if not new_exercise_json or "error" in new_exercise_json or not new_exercise_json.get("name"):
        print(f"SWAP FAILED. AI Output: {new_exercise_json}")
        raise HTTPException(
            status_code=400, 
            detail=f"Could not find a valid substitute. AI Response: {new_exercise_json.get('raw_content', 'Invalid JSON')}"
        )

    # 4. Update Logic (Remains the same)
    current_schedule = dict(plan.schedule)
    day_found = False
    
    for week_key, week_data in current_schedule.items():
        if isinstance(week_data, dict) and request.day_name in week_data:
            day_data = week_data[request.day_name]
            if isinstance(day_data, dict):
                exercises = day_data.get("exercises", [])
                
                for i, ex in enumerate(exercises):
                    if ex.get("name") == request.current_exercise_name:
                        # Merge Old Data with New Data
                        merged_exercise = {
                            "name": new_exercise_json.get("name"), # Guaranteed not null now
                            "sets": new_exercise_json.get("sets", ex.get("sets")),
                            "reps": new_exercise_json.get("reps", ex.get("reps")),
                            "rest": new_exercise_json.get("rest", ex.get("rest")),
                            "method": new_exercise_json.get("method", ex.get("method", "Standard")),
                            "intensity": new_exercise_json.get("intensity", ex.get("intensity", "")),
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

    print(f"ADJUSTING: {request.modification_type} for {request.day_name}")

    # 2. Extract the Target Exercises
    current_schedule = dict(plan.schedule)
    exercises_to_modify = []
    
    # Helper to find the day data
    day_data = None
    for week in current_schedule.values():
        if isinstance(week, dict) and request.day_name in week:
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
        modified_list = modifier.adjust_difficulty(exercises_to_modify)
        
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

        # Build profile data for the Pipeline
        user_profile_data = {
            "user_id": request.user_id,
            "days_per_week": request.new_days_per_week or 4,
            "location": request.new_location or user_profile.location, # Use new or stored
            "goals": request.new_goal or user_profile.goals,
            "equipment": user_profile.equipment_available, # Use stored equipment
            "age": user_profile.age,
            "gender": user_profile.gender,
            "weight": user_profile.weight,
            "height": user_profile.height
        }
        
        # 3. Inject History
        user_profile_data['previous_plan'] = str(old_plan.schedule) 
        user_profile_data['feedback'] = request.user_feedback

        print(f"GENERATING PROGRESSION for User: {request.user_id}")
        print(f"   Feedback: {request.user_feedback}")

        # 4. Run the Pipeline
        pipeline = WorkoutPipeline(user_profile=user_profile_data, equipment=user_profile.equipment_available)
        plan_json = pipeline.generate_plan()

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

@router.post("/plans/{plan_id}/restructure", response_model=WorkoutPlanResponse)
def restructure_plan(plan_id: str, request: RestructureRequest, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Plan
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        # 2. Re-construct User Profile
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        if not user_profile:
             raise HTTPException(status_code=404, detail="User Profile not found")

        # 3. Extract old exercises into a pool
        # We want the full database dict so the AI can filter by target_zone and force_type
        # First get all the names from the current schedule
        current_schedule = dict(plan.schedule)
        old_exercise_names = []
        for week in current_schedule.values():
            if isinstance(week, dict):
                for day_data in week.values():
                    if isinstance(day_data, dict):
                        for ex in day_data.get("exercises", []):
                            old_exercise_names.append(ex.get("name"))
                            
        # Now fetch the full dicts from pipeline's JSON
        # Since we just need the DB, we can instantiate an empty pipeline to read it
        temp_pipeline = WorkoutPipeline()
        exercise_pool = []
        for ex in temp_pipeline.all_exercises:
            if ex.get("name") in old_exercise_names:
                exercise_pool.append(ex)

        user_profile_data = {
            "user_id": request.user_id,
            "days_per_week": len([k for k, v in current_schedule.get("Week 1", {}).items() if v != "Rest" and isinstance(v, dict)]), # Keep the same active days
            "location": user_profile.location,
            "goals": user_profile.goals,
            "equipment": user_profile.equipment_available,
            "age": user_profile.age,
            "gender": user_profile.gender,
            "weight": user_profile.weight,
            "height": user_profile.height,
            "experience_level": getattr(user_profile, 'experience_level', 'Beginner')
        }

        print(f"RESTRUCTURING PLAN for User: {request.user_id} -> New Split: {request.new_split_name}")

        # 4. Run the Pipeline with force_split and exercise_pool
        pipeline = WorkoutPipeline(
            user_profile=user_profile_data, 
            equipment=user_profile.equipment_available,
            force_split=request.new_split_name,
            exercise_pool=exercise_pool
        )
        plan_json = pipeline.generate_plan()

        # 5. Save the updated plan
        plan.schedule = plan_json
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "schedule") 
        db.commit()

        return {
            "status": "success",
            "plan_id": plan.id,
            "message": f"Plan restructured to {request.new_split_name} successfully.",
            "workout_plan": json.dumps(plan_json)
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plans/{plan_id}/bulk-swap")
def bulk_swap_exercises(plan_id: str, request: BulkSwapRequest, db: Session = Depends(get_db)):
    try:
        # 1. Fetch Plan
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # 2. Fetch User Profile
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="User Profile not found")
        
        equipment = user_profile.equipment_available or LOCATION_EQUIPMENT.get(user_profile.location, [])
        goals = user_profile.goals or []
        
        print(f"BULK SWAP for User: {request.user_id} | {len(request.exercises)} exercises selected")
        
        # 3. Run the BulkExerciseSwapper agent
        swapper = BulkExerciseSwapper(
            equipment=equipment,
            plan_schedule=dict(plan.schedule),
            user_goals=goals
        )
        
        exercises_dict = [item.model_dump() for item in request.exercises]
        result = swapper.find_alternatives(exercises_dict)
        
        replacements = result.get("replacements", [])
        failures = result.get("failures", [])
        
        if not replacements:
            return {
                "status": "no_changes",
                "message": "Sorry, we couldn't find alternatives for the selected exercises.",
                "failures": failures
            }
        
        # 4. Apply replacements to the plan
        current_schedule = dict(plan.schedule)
        applied = 0
        
        for rep in replacements:
            day_name = rep["day_name"]
            original_name = rep["original_name"]
            new_ex = rep["new_exercise"]
            
            for week_key, week_data in current_schedule.items():
                if isinstance(week_data, dict) and day_name in week_data:
                    day_data = week_data[day_name]
                    if isinstance(day_data, dict):
                        exercises = day_data.get("exercises", [])
                        for i, ex in enumerate(exercises):
                            if ex.get("name") == original_name:
                                exercises[i] = {
                                    "name": new_ex.get("name", "Unknown"),
                                    "sets": new_ex.get("sets", "3"),
                                    "reps": new_ex.get("reps", "10"),
                                    "rest": new_ex.get("rest", "60s"),
                                    "method": new_ex.get("method", "Standard"),
                                    "intensity": new_ex.get("intensity", "RPE 7"),
                                    "notes": new_ex.get("notes", f"Replaced {original_name}")
                                }
                                applied += 1
                                break
        
        # 5. Save
        plan.schedule = current_schedule
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "schedule")
        db.commit()
        
        print(f"BULK SWAP COMPLETE: {applied} replaced, {len(failures)} failed")
        
        return {
            "status": "success",
            "message": f"Successfully replaced {applied} exercise(s).",
            "workout_plan": json.dumps(current_schedule),
            "replacements": replacements,
            "failures": failures
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- MODE 1: Equipment Alternatives (Deterministic) ---
@router.post("/plans/{plan_id}/equipment-alternatives")
def get_equipment_alternatives(plan_id: str, request: EquipmentAlternativesRequest, db: Session = Depends(get_db)):
    try:
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="User Profile not found")
        
        equipment = user_profile.equipment_available or LOCATION_EQUIPMENT.get(user_profile.location, [])
        
        pipeline = WorkoutPipeline(equipment=equipment)
        alternatives = pipeline.find_equipment_alternatives(request.exercise_name, equipment)
        
        return {
            "exercise_name": request.exercise_name,
            "alternatives": [
                {"name": ex["name"], "equipment": ex.get("equipment", []), "mechanics": ex.get("mechanics", "")}
                for ex in alternatives
            ]
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- MODE 1: Apply Equipment Swap (no AI) ---
@router.post("/plans/{plan_id}/apply-equipment-swap")
def apply_equipment_swap(plan_id: str, request: ApplyEquipmentSwapRequest, db: Session = Depends(get_db)):
    """Swap an exercise with the chosen alternative."""
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        current_schedule = dict(plan.schedule)
        
        # Find the day and the exercise slot
        for week_key, week_data in current_schedule.items():
            if isinstance(week_data, dict) and request.day_name in week_data:
                day_data = week_data[request.day_name]
                if isinstance(day_data, dict):
                    exercises = day_data.get("exercises", [])
                    for i, ex in enumerate(exercises):
                        if ex.get("name") == request.exercise_name:
                            exercises[i] = {
                                **ex,
                                "name": request.new_exercise_name,
                                "notes": f"Swapped from {request.exercise_name}"
                            }
                            break
        
        plan.schedule = current_schedule
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "schedule")
        db.commit()
        
        return {"status": "success", "workout_plan": json.dumps(current_schedule)}
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- MODE 2: Smart AI Swap ---
@router.post("/plans/{plan_id}/smart-swap")
def smart_swap_exercise(plan_id: str, request: SmartSwapRequest, db: Session = Depends(get_db)):
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        user_profile = db.query(UserProfile).filter(UserProfile.username == request.user_id).first()
        if not user_profile:
            raise HTTPException(status_code=404, detail="User Profile not found")
        
        equipment = user_profile.equipment_available or LOCATION_EQUIPMENT.get(user_profile.location, [])
        goals = user_profile.goals or []
        
        # Get the current day's exercises (excluding the one being replaced)
        current_schedule = dict(plan.schedule)
        day_exercises = []
        for week_key, week_data in current_schedule.items():
            if isinstance(week_data, dict) and request.day_name in week_data:
                day_data = week_data[request.day_name]
                if isinstance(day_data, dict):
                    day_exercises = [
                        ex for ex in day_data.get("exercises", [])
                        if ex.get("name") != request.exercise_name
                    ]
        
        pipeline = WorkoutPipeline(equipment=equipment)
        result = pipeline.find_smart_replacement(
            exercise_name=request.exercise_name,
            target_zone_override=request.target_zone,
            day_exercises=day_exercises,
            user_goals=goals,
            equipment=equipment
        )
        
        if not result:
            return {"status": "no_alternatives", "message": "No exercises available for this target zone with your equipment."}
        
        # Apply the swap to the plan
        for week_key, week_data in current_schedule.items():
            if isinstance(week_data, dict) and request.day_name in week_data:
                day_data = week_data[request.day_name]
                if isinstance(day_data, dict):
                    exercises = day_data.get("exercises", [])
                    for i, ex in enumerate(exercises):
                        if ex.get("name") == request.exercise_name:
                            exercises[i] = {
                                "name": result.get("name", "Unknown"),
                                "sets": result.get("sets", "3"),
                                "reps": result.get("reps", "10"),
                                "rest": result.get("rest", "60s"),
                                "method": result.get("method", "Standard"),
                                "intensity": result.get("intensity", "RPE 7"),
                                "notes": result.get("notes", "")
                            }
                            break
        
        plan.schedule = current_schedule
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "schedule")
        db.commit()
        
        return {
            "status": "success",
            "workout_plan": json.dumps(current_schedule),
            "replacement": result
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))