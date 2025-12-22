from fastapi import APIRouter
from src.api.schemas import WorkoutRequest, WorkoutResponse

# Create a Router (like a mini-app)
router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "running", "message": "LazyTrainer Brain is Active 🧠"}

@router.post("/generate", response_model=WorkoutResponse)
def generate_workout(request: WorkoutRequest):
    print(f"Received request for User {request.user_id}")
    return {
        "status": "processing",
        "task_id": "12345-fake-id",
        "message": f"Agent is researching exercises for {request.goal}..."
    }