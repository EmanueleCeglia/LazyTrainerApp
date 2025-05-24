from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import sys

# risale di due cartelle e punta a personaltrainers/src
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(root, 'personaltrainers', 'src')
sys.path.insert(0, src_dir)

from personaltrainers import test_crew

app = FastAPI()

# NUOVO MODELLO per /workout  
class WorkoutData(BaseModel):
    level: str
    train_target: str
    focus_muscle: bool          # ← IMPORTANTE: bool, non str
    muscles: List[str]               # ← IMPORTANTE: "muscles", non "muscle"
    duration_minutes: int
    location: str
    equipment: List[str] 



# Define the endpoint that receives the JSON data from the Android app
@app.post("/workout")
async def process_workout(payload: WorkoutData):

    try:
        # Usa il tuo test_crew con i dati del questionario
        generated_text = test_crew.test_crew(payload=payload)
        
        return JSONResponse(content={"generated_text": generated_text}, headers={"Content-Type": "application/json; charset=utf-8"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


