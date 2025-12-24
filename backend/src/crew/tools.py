import os
from typing import List, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from sqlalchemy import text
from openai import OpenAI

# Import our Database Connection and Models
from src.database.connection import SessionLocal
from src.database.models import Exercise

# --- CHANGED: Simplified Inputs for AI Stability ---
class ExerciseSearchInput(BaseModel):
    query: str = Field(..., description="The goal of the exercise (e.g., 'Build chest mass', 'Explosive leg power').")
    target_zone: str = Field(..., description="The biomechanical zone: 'Upper', 'Lower', 'Core', or 'Full Body'.")
    force_type: Optional[str] = Field(None, description="The movement pattern: 'Push', 'Pull', 'Squat', 'Hinge', 'Lunge', 'Static'.")
    
    # We changed List[str] to str. The AI will send "Dumbbell, Bench". We split it manually.
    available_equipment: str = Field(..., description="A comma-separated string of equipment (e.g. 'Dumbbell, Barbell').")
    user_injuries: str = Field(default="", description="A comma-separated string of injuries (e.g. 'knee_pain, shoulder_pain').")

class ExerciseRetrieverTool(BaseTool):
    name: str = "Exercise Knowledge Base"
    description: str = (
        "Useful for searching specific exercises based on biomechanics, equipment, and goals. "
        "Input should be a specific query with equipment and injuries as comma-separated strings."
    )
    args_schema: Type[BaseModel] = ExerciseSearchInput

    def _run(self, query: str, target_zone: str, available_equipment: str, user_injuries: str, force_type: str = None) -> str:
        session = SessionLocal()
        client = OpenAI()
        
        try:
            # --- 1. PRE-PROCESSING (Manual List Conversion) ---
            # We convert the string "Dumbbell, Bench" -> ['Dumbbell', 'Bench']
            equipment_list = [item.strip() for item in available_equipment.split(',') if item.strip()]
            injuries_list = [item.strip() for item in user_injuries.split(',') if item.strip()]

            print(f"\n🔍 AGENT TOOL CALL: Searching for '{query}'")
            print(f"   Zone: {target_zone} | Force: {force_type}")
            print(f"   Equip: {equipment_list} | Injuries: {injuries_list}")

            # --- 2. GENERATE EMBEDDING ---
            response = client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_vector = response.data[0].embedding

            # --- 3. BUILD THE HYBRID QUERY ---
            sql_query = session.query(Exercise)

            # A. Hard Filters
            sql_query = sql_query.filter(Exercise.target_zone == target_zone)
            
            if force_type and force_type != "None": # Handle generic string 'None' from AI
                sql_query = sql_query.filter(Exercise.force_type == force_type)

            # B. Safety Filter
            if injuries_list:
                sql_query = sql_query.filter(~Exercise.contraindications.overlap(injuries_list))

            # C. Equipment Filter
            # Ensure the exercise equipment is contained in the user's list
            sql_query = sql_query.filter(Exercise.equipment.contained_by(equipment_list))

            # --- 4. SEMANTIC RANKING ---
            sql_query = sql_query.order_by(Exercise.embedding.cosine_distance(query_vector))

            # --- 5. FETCH RESULTS ---
            results = sql_query.limit(5).all()

            if not results:
                return f"No exercises found for {target_zone} ({force_type}) with equipment {equipment_list}. Try broadening the search."

            # --- 6. FORMAT OUTPUT ---
            output_text = ""
            for ex in results:
                output_text += f"NAME: {ex.name}\n"
                output_text += f"TYPE: {ex.mechanics} {ex.force_type}\n"
                output_text += f"MUSCLES: {ex.muscle_group}\n"
                output_text += f"EQUIPMENT: {', '.join(ex.equipment)}\n"
                output_text += f"INSTRUCTIONS: {ex.instructions[:100]}...\n"
                output_text += "---\n"
            
            return output_text

        except Exception as e:
            return f"Error querying database: {str(e)}"
        finally:
            session.close()