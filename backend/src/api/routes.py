import uuid
import json
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.ai.pipeline import WorkoutPipeline, WorkoutModifier, BulkExerciseSwapper
from src.database.connection import get_db
from src.database.models import WorkoutPlan, UserProfile
from src.api.auth import get_current_user
from src.api.schemas import (
    UserProfileRequest,
    WorkoutPlanResponse,
    ExerciseSwapRequest,
    DifficultyModificationRequest,
    ProgressionRequest,
    RestructureRequest,
    BulkSwapRequest,
    EquipmentAlternativesRequest,
    SmartSwapRequest,
    ApplyEquipmentSwapRequest,
    PlanSummary,
    PlanDetail,
)

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
    except json.JSONDecodeError:
        print(f"   Raw Content: {raw_string}")
        # Fallback: Return a partial object so the app doesn't crash
        return {"error": "Failed to parse AI response", "raw_content": raw_string}


def get_owned_plan(plan_id: str, db: Session, current_user: UserProfile) -> WorkoutPlan:
    """
    Fetch a plan and verify the caller owns it.

    Returns 404 (not 403) for someone else's plan so we never confirm that a
    given plan_id exists to a user who has no business knowing.
    """
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == current_user.username)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


def resolve_equipment(user_profile: UserProfile) -> list:
    """Stored equipment if we have it, otherwise the base kit for their location."""
    return user_profile.equipment_available or LOCATION_EQUIPMENT.get(
        user_profile.location, LOCATION_EQUIPMENT["Gym"]
    )


def find_day(schedule: dict, day_name: str):
    """Locate a day's data inside the {week: {day: ...}} schedule structure."""
    for week_data in schedule.values():
        if isinstance(week_data, dict) and day_name in week_data:
            return week_data[day_name]
    return None


def replace_exercise(schedule: dict, day_name: str, exercise_name: str, new_exercise: dict) -> bool:
    """Swap one exercise in place. Returns False if the exercise wasn't there."""
    day_data = find_day(schedule, day_name)
    if not isinstance(day_data, dict):
        return False
    exercises = day_data.get("exercises", [])
    for i, ex in enumerate(exercises):
        if ex.get("name") == exercise_name:
            exercises[i] = new_exercise
            return True
    return False


def save_schedule(plan: WorkoutPlan, schedule: dict, db: Session):
    """JSONB columns need an explicit flag_modified or SQLAlchemy won't persist the change."""
    plan.schedule = schedule
    flag_modified(plan, "schedule")
    db.commit()


@router.get("/")
def health_check():
    return {"status": "running", "message": "LazyTrainer Brain is Active"}


# --- PLAN RETRIEVAL ---
@router.get("/plans", response_model=list[PlanSummary])
def list_plans(db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Every plan belonging to the logged-in user, newest first."""
    plans = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.user_id == current_user.username)
        .order_by(WorkoutPlan.created_at.desc())
        .all()
    )
    return [
        PlanSummary(
            plan_id=p.id,
            name=p.name,
            status=p.status,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in plans
    ]


@router.get("/plans/{plan_id}", response_model=PlanDetail)
def get_plan(plan_id: str, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Reload a saved plan - this is what lets a program survive a logout."""
    plan = get_owned_plan(plan_id, db, current_user)
    return PlanDetail(
        plan_id=plan.id,
        name=plan.name,
        status=plan.status,
        created_at=plan.created_at.isoformat() if plan.created_at else None,
        workout_plan=json.dumps(plan.schedule),
    )


@router.post("/generate", response_model=WorkoutPlanResponse)
def generate_workout(request: UserProfileRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        # --- 2. MERGE EQUIPMENT ---
        base_kit = LOCATION_EQUIPMENT.get(request.location, [])
        combined_equipment = sorted(set(base_kit + request.equipment))

        user_data = request.model_dump()
        user_data['equipment'] = combined_equipment
        # The owner is whoever holds the token - never what the client claims.
        user_data['user_id'] = current_user.username

        # --- SAVE USER CONTEXT TO DB (The "Memory") ---
        current_user.location = request.location
        current_user.equipment_available = combined_equipment
        current_user.goals = request.goals
        current_user.age = request.age
        current_user.gender = request.gender
        current_user.weight = request.weight
        current_user.height = request.height
        current_user.experience_level = request.experience_level
        print(f"Updated profile for {current_user.username}")

        db.commit()  # Save immediately

        print(f"\nSTARTING PIPELINE for User: {current_user.username}")

        # --- 3. RUN PIPELINE ---
        pipeline = WorkoutPipeline(user_profile=user_data, equipment=combined_equipment)
        plan_json = pipeline.generate_plan()

        # Generate a unique ID for this plan
        plan_id = str(uuid.uuid4())

        new_plan = WorkoutPlan(
            id=plan_id,
            user_id=current_user.username,
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

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}/swap")
def swap_exercise(plan_id: str, request: ExerciseSwapRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    # 1. Fetch Plan (ownership enforced)
    plan = get_owned_plan(plan_id, db, current_user)

    print(f"SWAPPING: {request.current_exercise_name} on {request.day_name}")

    # --- 2. FETCH MEMORY ---
    saved_equipment = current_user.equipment_available
    if saved_equipment:
        print(f"   Memory: Found {len(saved_equipment)} items for user.")
    else:
        print("   Memory Warning: User equipment empty. Defaulting to Gym context.")
        saved_equipment = LOCATION_EQUIPMENT["Gym"]

    # --- 3. Run AI with Context ---
    try:
        modifier = WorkoutModifier(request, saved_equipment)
        new_exercise_json = modifier.find_substitute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Critical Error: {str(e)}")

    # GUARD CLAUSE
    if not new_exercise_json or "error" in new_exercise_json or not new_exercise_json.get("name"):
        print(f"SWAP FAILED. AI Output: {new_exercise_json}")
        raise HTTPException(
            status_code=400,
            detail=f"Could not find a valid substitute. AI Response: {(new_exercise_json or {}).get('raw_content', 'Invalid JSON')}"
        )

    # 4. Update Logic
    current_schedule = dict(plan.schedule)
    day_data = find_day(current_schedule, request.day_name)
    old_exercise = None
    if isinstance(day_data, dict):
        old_exercise = next(
            (ex for ex in day_data.get("exercises", []) if ex.get("name") == request.current_exercise_name),
            None
        )

    if old_exercise is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exercise '{request.current_exercise_name}' not found in {request.day_name}"
        )

    # Merge Old Data with New Data
    merged_exercise = {
        "name": new_exercise_json.get("name"),  # Guaranteed not null now
        "sets": new_exercise_json.get("sets", old_exercise.get("sets")),
        "reps": new_exercise_json.get("reps", old_exercise.get("reps")),
        "rest": new_exercise_json.get("rest", old_exercise.get("rest")),
        "method": new_exercise_json.get("method", old_exercise.get("method", "Standard")),
        "intensity": new_exercise_json.get("intensity", old_exercise.get("intensity", "")),
        "notes": new_exercise_json.get("notes", f"Swapped from {request.current_exercise_name}")
    }
    replace_exercise(current_schedule, request.day_name, request.current_exercise_name, merged_exercise)

    # 5. Save
    save_schedule(plan, current_schedule, db)

    return {
        "status": "success",
        "message": f"Swapped {request.current_exercise_name} for {new_exercise_json.get('name')}",
        "new_exercise": merged_exercise
    }


@router.put("/plans/{plan_id}/adjust")
def adjust_difficulty(plan_id: str, request: DifficultyModificationRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    # 1. Fetch Plan (ownership enforced)
    plan = get_owned_plan(plan_id, db, current_user)

    print(f"ADJUSTING: {request.modification_type} for {request.day_name}")

    # 2. Extract the Target Exercises
    current_schedule = dict(plan.schedule)
    day_data = find_day(current_schedule, request.day_name)

    if not isinstance(day_data, dict):
        raise HTTPException(status_code=404, detail=f"{request.day_name} not found in plan")

    all_exercises = day_data.get("exercises", [])

    # Filter: If target_names provided, select only those. Else, select ALL.
    if request.target_exercise_names:
        exercises_to_modify = [ex for ex in all_exercises if ex.get('name') in request.target_exercise_names]
    else:
        exercises_to_modify = all_exercises

    if not exercises_to_modify:
        raise HTTPException(status_code=404, detail="No matching exercises found to modify")

    # 3. Run AI Modifier
    try:
        # adjust_difficulty only rewrites numbers, so the equipment list is irrelevant here.
        modifier = WorkoutModifier(request, [])
        modified_list = modifier.adjust_difficulty(exercises_to_modify)

        # Validation: Ensure we got a list back
        if isinstance(modified_list, dict):
            # Sometimes LLM wraps list in {"exercises": [...]}
            modified_list = modified_list.get("exercises", [modified_list])
        if not isinstance(modified_list, list):
            modified_list = [modified_list]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

    # 4. Merge Back (The Surgery)
    updated_count = 0
    for new_ex in modified_list:
        if not isinstance(new_ex, dict):
            continue
        for i, old_ex in enumerate(all_exercises):
            if old_ex.get("name") == new_ex.get("name"):
                all_exercises[i] = new_ex  # Replace with new parameters
                updated_count += 1

    # 5. Save
    save_schedule(plan, current_schedule, db)

    return {
        "status": "success",
        "message": f"Updated {updated_count} exercises.",
        "modified_exercises": modified_list
    }


@router.post("/generate/next", response_model=WorkoutPlanResponse)
def generate_next_block(request: ProgressionRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        # 1. Fetch Previous Plan (ownership enforced)
        old_plan = get_owned_plan(request.previous_plan_id, db, current_user)

        # 2. Build profile data for the Pipeline from the authenticated user
        equipment = resolve_equipment(current_user)
        user_profile_data = {
            "user_id": current_user.username,
            "days_per_week": request.new_days_per_week or 4,
            "location": request.new_location or current_user.location,  # Use new or stored
            "goals": request.new_goal or current_user.goals,
            "equipment": equipment,  # Use stored equipment
            "age": current_user.age,
            "gender": current_user.gender,
            "weight": current_user.weight,
            "height": current_user.height,
            "experience_level": current_user.experience_level or "Beginner",
        }

        # 3. Inject History
        user_profile_data['previous_plan'] = str(old_plan.schedule)
        user_profile_data['feedback'] = request.user_feedback

        print(f"GENERATING PROGRESSION for User: {current_user.username}")
        print(f"   Feedback: {request.user_feedback}")

        # 4. Run the Pipeline
        pipeline = WorkoutPipeline(user_profile=user_profile_data, equipment=equipment)
        plan_json = pipeline.generate_plan()

        # 5. Save New Plan
        new_plan_id = str(uuid.uuid4())
        new_plan = WorkoutPlan(
            id=new_plan_id,
            user_id=current_user.username,
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

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/restructure", response_model=WorkoutPlanResponse)
def restructure_plan(plan_id: str, request: RestructureRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        # 1. Fetch Plan (ownership enforced)
        plan = get_owned_plan(plan_id, db, current_user)

        # 2. Extract old exercises into a pool
        current_schedule = dict(plan.schedule)
        old_exercise_names = []
        for week in current_schedule.values():
            if isinstance(week, dict):
                for day_data in week.values():
                    if isinstance(day_data, dict):
                        for ex in day_data.get("exercises", []):
                            old_exercise_names.append(ex.get("name"))

        # Fetch the full catalog dicts so the Selector can filter by zone/force
        temp_pipeline = WorkoutPipeline()
        exercise_pool = [ex for ex in temp_pipeline.all_exercises if ex.get("name") in old_exercise_names]

        equipment = resolve_equipment(current_user)
        user_profile_data = {
            "user_id": current_user.username,
            # Keep the same number of active days
            "days_per_week": len([
                v for v in current_schedule.get("Week 1", {}).values()
                if isinstance(v, dict)
            ]) or 4,
            "location": current_user.location,
            "goals": current_user.goals,
            "equipment": equipment,
            "age": current_user.age,
            "gender": current_user.gender,
            "weight": current_user.weight,
            "height": current_user.height,
            "experience_level": current_user.experience_level or "Beginner",
        }

        print(f"RESTRUCTURING PLAN for User: {current_user.username} -> New Split: {request.new_split_name}")

        # 3. Run the Pipeline with force_split and exercise_pool
        pipeline = WorkoutPipeline(
            user_profile=user_profile_data,
            equipment=equipment,
            force_split=request.new_split_name,
            exercise_pool=exercise_pool
        )
        plan_json = pipeline.generate_plan()

        # 4. Save the updated plan
        plan.name = plan_json.get("plan_name", plan.name)
        save_schedule(plan, plan_json, db)

        return {
            "status": "success",
            "plan_id": plan.id,
            "message": f"Plan restructured to {request.new_split_name} successfully.",
            "workout_plan": json.dumps(plan_json)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/bulk-swap")
def bulk_swap_exercises(plan_id: str, request: BulkSwapRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        # 1. Fetch Plan (ownership enforced)
        plan = get_owned_plan(plan_id, db, current_user)

        equipment = resolve_equipment(current_user)
        goals = current_user.goals or []

        print(f"BULK SWAP for User: {current_user.username} | {len(request.exercises)} exercises selected")

        # 2. Run the BulkExerciseSwapper agent
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

        # 3. Apply replacements to the plan
        current_schedule = dict(plan.schedule)
        applied = 0

        for rep in replacements:
            new_ex = rep["new_exercise"]
            merged = {
                "name": new_ex.get("name", "Unknown"),
                "sets": new_ex.get("sets", "3"),
                "reps": new_ex.get("reps", "10"),
                "rest": new_ex.get("rest", "60s"),
                "method": new_ex.get("method", "Standard"),
                "intensity": new_ex.get("intensity", "RPE 7"),
                "notes": new_ex.get("notes", f"Replaced {rep['original_name']}")
            }
            if replace_exercise(current_schedule, rep["day_name"], rep["original_name"], merged):
                applied += 1
            else:
                failures.append({
                    "day_name": rep["day_name"],
                    "exercise_name": rep["original_name"],
                    "reason": "Exercise no longer present in that day."
                })

        # 4. Save
        save_schedule(plan, current_schedule, db)

        print(f"BULK SWAP COMPLETE: {applied} replaced, {len(failures)} failed")

        return {
            "status": "success",
            "message": f"Successfully replaced {applied} exercise(s).",
            "workout_plan": json.dumps(current_schedule),
            "replacements": replacements,
            "failures": failures
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- MODE 1: Equipment Alternatives (Deterministic) ---
@router.post("/plans/{plan_id}/equipment-alternatives")
def get_equipment_alternatives(plan_id: str, request: EquipmentAlternativesRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        get_owned_plan(plan_id, db, current_user)

        equipment = resolve_equipment(current_user)

        pipeline = WorkoutPipeline(equipment=equipment)
        alternatives = pipeline.find_equipment_alternatives(request.exercise_name, equipment)

        return {
            "exercise_name": request.exercise_name,
            "alternatives": [
                {"name": ex["name"], "equipment": ex.get("equipment", []), "mechanics": ex.get("mechanics", "")}
                for ex in alternatives
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- MODE 1: Apply Equipment Swap (no AI) ---
@router.post("/plans/{plan_id}/apply-equipment-swap")
def apply_equipment_swap(plan_id: str, request: ApplyEquipmentSwapRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    """Swap an exercise with the chosen alternative, keeping its sets/reps."""
    try:
        plan = get_owned_plan(plan_id, db, current_user)

        current_schedule = dict(plan.schedule)
        day_data = find_day(current_schedule, request.day_name)
        if not isinstance(day_data, dict):
            raise HTTPException(status_code=404, detail=f"{request.day_name} not found in plan")

        old_exercise = next(
            (ex for ex in day_data.get("exercises", []) if ex.get("name") == request.exercise_name),
            None
        )
        if old_exercise is None:
            raise HTTPException(
                status_code=404,
                detail=f"Exercise '{request.exercise_name}' not found in {request.day_name}"
            )

        replace_exercise(current_schedule, request.day_name, request.exercise_name, {
            **old_exercise,
            "name": request.new_exercise_name,
            "notes": f"Swapped from {request.exercise_name}"
        })

        save_schedule(plan, current_schedule, db)

        return {"status": "success", "workout_plan": json.dumps(current_schedule)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- MODE 2: Smart AI Swap ---
@router.post("/plans/{plan_id}/smart-swap")
def smart_swap_exercise(plan_id: str, request: SmartSwapRequest, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):
    try:
        plan = get_owned_plan(plan_id, db, current_user)

        equipment = resolve_equipment(current_user)
        goals = current_user.goals or []

        # Get the current day's exercises (excluding the one being replaced)
        current_schedule = dict(plan.schedule)
        day_data = find_day(current_schedule, request.day_name)
        if not isinstance(day_data, dict):
            raise HTTPException(status_code=404, detail=f"{request.day_name} not found in plan")

        if not any(ex.get("name") == request.exercise_name for ex in day_data.get("exercises", [])):
            raise HTTPException(
                status_code=404,
                detail=f"Exercise '{request.exercise_name}' not found in {request.day_name}"
            )

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
            return {
                "status": "no_alternatives",
                "message": "No exercises available for this target zone with your equipment."
            }

        replace_exercise(current_schedule, request.day_name, request.exercise_name, {
            "name": result.get("name", "Unknown"),
            "sets": result.get("sets", "3"),
            "reps": result.get("reps", "10"),
            "rest": result.get("rest", "60s"),
            "method": result.get("method", "Standard"),
            "intensity": result.get("intensity", "RPE 7"),
            "notes": result.get("notes", "")
        })

        save_schedule(plan, current_schedule, db)

        return {
            "status": "success",
            "workout_plan": json.dumps(current_schedule),
            "replacement": result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
