from pydantic import BaseModel
from typing import List, Optional

class WorkoutRequest(BaseModel):
    user_id: int
    goal: str
    injuries: List[str] = []

class WorkoutResponse(BaseModel):
    status: str
    task_id: str
    message: str