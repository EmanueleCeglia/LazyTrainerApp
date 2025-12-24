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
    Triggers the AI Crew to generate a workout based on the user profile.
    """
    try:
        # 1. Log the Request
        print(f"\n🚀 STARTING AI AGENT for User: {request.user_id}")
        
        # 2. Convert Pydantic Model to Dict (CrewAI expects a dict)
        user_data = request.model_dump() # Use .dict() if you are on an older Pydantic version

        # 3. Initialize and Run the Crew
        workout_crew = WorkoutCrew(user_profile=user_data)
        result = workout_crew.run()

        # 4. Return the result
        return {
            "status": "success",
            "plan_id": str(uuid.uuid4()),
            "message": "Workout generated successfully.",
            "workout_plan": str(result) # The Markdown output from the AI
        }

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))