import uuid
from fastapi import APIRouter, HTTPException
from src.api.schemas import UserProfileRequest, WorkoutPlanResponse
from src.crew.main import WorkoutCrew

router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "running", "message": "LazyTrainer Brain is Active 🧠"}

@router.post("/generate", response_model=WorkoutPlanResponse)
def generate_workout(request: UserProfileRequest):
    """
    Triggers the AI Crew with the new detailed User Profile.
    """
    try:
        # 1. Log the Request (Updated for new fields)
        print(f"\n🚀 STARTING AI AGENT for User: {request.user_id}")
        print(f"   Split: {request.split_type} ({request.days_per_week} days)")
        print(f"   Location: {request.location}")
        print(f"   Zones: {request.target_zone}")
        print(f"   Equip: {len(request.equipment)} items")
        
        # 2. Convert to Dict for CrewAI
        user_data = request.model_dump()

        # 3. Run the Crew
        workout_crew = WorkoutCrew(user_profile=user_data)
        result = workout_crew.run()

        # 4. Return result
        return {
            "status": "success",
            "plan_id": str(uuid.uuid4()),
            "message": "Workout generated successfully.",
            "workout_plan": str(result)
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))