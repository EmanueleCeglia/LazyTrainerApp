import os
from typing import List, Union, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from sqlalchemy import cast, or_
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from openai import OpenAI

from src.database.connection import SessionLocal
from src.database.models import Exercise

# --- 1. STRICT INPUT SCHEMA ---
# We provide the AI with the EXACT menus of options available in the DB.
class ExerciseSearchInput(BaseModel):
    query: str = Field(
        ..., 
        description="A description of the movement or goal (e.g., 'Chest isolation', 'Quads builder'). Used for semantic search."
    )
    
    target_zone: Union[List[str], str, None] = Field(
        default=None, 
        description=(
            "Strict Filter. MUST be one or more of: "
            "['Upper', 'Lower', 'Core', 'Full Body', 'Cardio']. "
            "Example: ['Upper']"
        )
    )
    
    force_type: Union[List[str], str, None] = Field(
        default=None, 
        description=(
            "Strict Filter. MUST be one or more of: "
            "['Push', 'Pull', 'Hinge', 'Squat', 'Lunge', 'Dynamic', 'Static']. "
            "Example: ['Push']"
        )
    )
    
    available_equipment: Union[List[str], str] = Field(
        ..., 
        description="The User's Inventory (e.g. ['Dumbbells', 'Barbell']). The tool automatically checks if the exercise fits this list."
    )
    
    user_injuries: Union[List[str], str] = Field(
        default=[], 
        description="List of injuries to filter out contraindicated exercises."
    )

class ExerciseRetrieverTool(BaseTool):
    name: str = "Exercise Knowledge Base"
    description: str = (
        "Search for exercises. You MUST use the 'target_zone' and 'force_type' arguments "
        "if the user specifies a body part or movement pattern. "
        "This tool handles equipment validation automatically."
    )
    args_schema: Type[BaseModel] = ExerciseSearchInput

    def _run(self, query: str, available_equipment: Union[List[str], str], user_injuries: Union[List[str], str], target_zone: Union[List[str], str] = None, force_type: Union[List[str], str] = None) -> str:
        session = SessionLocal()
        client = OpenAI()
        
        try:
            # --- 1. CLEANING HELPER ---
            def parse_list(input_data):
                if not input_data: return []
                if isinstance(input_data, list):
                    return [str(i).strip() for i in input_data]
                if isinstance(input_data, str):
                    # Handle LLM hallucinations like "['Upper']" string
                    clean = input_data.replace('[', '').replace(']', '').replace("'", '').replace('"', '')
                    return [i.strip() for i in clean.split(',') if i.strip()]
                return []

            raw_equipment = parse_list(available_equipment)
            injuries_list = parse_list(user_injuries)
            zones_list = parse_list(target_zone)
            forces_list = parse_list(force_type)

            # --- 2. DATA NORMALIZATION ---
            # Ensure Title Case for DB matching
            final_equipment = [item.title() for item in raw_equipment]
            
            # CRITICAL: Always add Bodyweight. 
            # If user has ['Dumbbells'], they implicitly have ['Dumbbells', 'Bodyweight'].
            if "Bodyweight" not in final_equipment:
                final_equipment.append("Bodyweight")

            print(f"\n🔍 TOOL SEARCH: '{query}'")
            print(f"   Inventory: {final_equipment}")
            print(f"   Strict Filters: Zone={zones_list} | Force={forces_list}")

            # --- 3. EMBEDDINGS (Semantic Search) ---
            response = client.embeddings.create(input=query, model="text-embedding-3-small")
            query_vector = response.data[0].embedding

            # --- 4. BUILD SQL QUERY ---
            sql_query = session.query(Exercise)

            # A. Strict Zone Filter
            if zones_list:
                sql_query = sql_query.filter(Exercise.target_zone.in_(zones_list))
            
            # B. Strict Force Filter
            if forces_list:
                sql_query = sql_query.filter(Exercise.force_type.in_(forces_list))
            
            # C. Injury Exclusion
            if injuries_list:
                # Exclude if ANY user injury overlaps with exercise contraindications
                sql_query = sql_query.filter(~cast(Exercise.contraindications, ARRAY(VARCHAR)).op('&&')(cast(injuries_list, ARRAY(VARCHAR))))
            
            # D. Equipment Subset Logic (<@)
            # Checks if Exercise Requirements are contained within User Inventory
            if final_equipment:
                sql_query = sql_query.filter(
                    cast(Exercise.equipment, ARRAY(VARCHAR)).op('<@')(cast(final_equipment, ARRAY(VARCHAR)))
                )

            # E. Semantic Ranking
            sql_query = sql_query.order_by(Exercise.embedding.cosine_distance(query_vector))
            
            # F. Execute
            results = sql_query.limit(10).all()

            if not results:
                # Return a helpful error message so the Agent knows WHY it failed
                return (
                    f"No exercises found matching criteria.\n"
                    f"Checked against Inventory: {final_equipment}\n"
                    f"Filters Applied: Zone={zones_list}, Force={forces_list}\n"
                    f"Suggestion: Try removing the specific force type or broadening the query."
                )

            # --- 5. FORMAT OUTPUT ---
            output_text = f"Found {len(results)} valid exercises:\n"
            
            for ex in results:
                # Display equipment cleanly
                equip_display = ex.equipment
                if isinstance(equip_display, list):
                    equip_str = ", ".join(equip_display)
                else:
                    equip_str = str(equip_display).replace('{', '').replace('}', '').replace('"', '')

                output_text += f"NAME: {ex.name}\n"
                output_text += f"DETAILS: {ex.target_zone} | {ex.force_type}\n"
                output_text += f"REQUIRES: {equip_str}\n"
                output_text += f"NOTE: {ex.instructions[:120]}...\n"
                output_text += "---\n"
            
            return output_text

        except Exception as e:
            print(f"❌ TOOL ERROR: {str(e)}")
            return f"Database Error: {str(e)}"
        finally:
            session.close()