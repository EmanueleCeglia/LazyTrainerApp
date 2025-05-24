from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
import sys
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info("=== INIZIO ENDPOINT ===")
    logger.info(f"Payload ricevuto: {payload}")
    logger.info("=== INIZIO ENDPOINT ===")
    logger.info(f"Payload RAW: {payload}")
    logger.info(f"Level: '{payload.level}' (type: {type(payload.level)})")
    logger.info(f"Train target: '{payload.train_target}' (type: {type(payload.train_target)})")
    logger.info(f"Focus muscle: {payload.focus_muscle} (type: {type(payload.focus_muscle)})")
    logger.info(f"Muscles: {payload.muscles} (type: {type(payload.muscles)})")
    logger.info(f"Duration: {payload.duration_minutes} (type: {type(payload.duration_minutes)})")
    logger.info(f"Location: '{payload.location}' (type: {type(payload.location)})")
    logger.info(f"Equipment: {payload.equipment} (type: {type(payload.equipment)})")
    try:
        logger.info("Chiamando test_crew.test_crew()...")
        generated_text = test_crew.test_crew(payload=payload)
        logger.info(f"Risultato da test_crew: {generated_text}")
        
        response = JSONResponse(
            content={"generated_text": generated_text}, 
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        logger.info("=== FINE ENDPOINT (SUCCESS) ===")
        return response
    
    except Exception as e:
        logger.error(f"Errore in process_workout: {str(e)}")
        logger.error(f"Tipo errore: {type(e)}")
        raise HTTPException(status_code=500, detail=str(e))


