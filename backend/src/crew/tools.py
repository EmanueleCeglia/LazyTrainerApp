import os
from typing import List, Union, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from sqlalchemy import text, cast  # <--- Added cast
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR # <--- Added types
from openai import OpenAI

from src.database.connection import SessionLocal
from src.database.models import Exercise

class ExerciseSearchInput(BaseModel):
    query: str = Field(..., description="The goal (e.g. 'Build Chest').")
    
    target_zone: Union[List[str], str, None] = Field(default=None, description="List of zones: ['Upper', 'Lower'].")
    force_type: Union[List[str], str, None] = Field(default=None, description="List of types: ['Push', 'Pull'].")
    
    available_equipment: Union[List[str], str] = Field(..., description="List of equipment.")
    user_injuries: Union[List[str], str] = Field(default=[], description="List of injuries.")

class ExerciseRetrieverTool(BaseTool):
    name: str = "Exercise Knowledge Base"
    description: str = "Search for exercises using strict SQL filtering on Zone/Equipment/Injuries."
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
                    clean = input_data.replace('[', '').replace(']', '').replace("'", '').replace('"', '')
                    return [i.strip() for i in clean.split(',') if i.strip()]
                return []

            equipment_list = parse_list(available_equipment)
            injuries_list = parse_list(user_injuries)
            zones_list = parse_list(target_zone)
            forces_list = parse_list(force_type)

            print(f"\n🔍 STRICT SQL SEARCH: '{query}'")
            print(f"   Zones: {zones_list} | Forces: {forces_list}")
            print(f"   Equip: {equipment_list} | Inj: {injuries_list}")

            # --- 2. EMBEDDINGS ---
            try:
                response = client.embeddings.create(input=query, model="text-embedding-3-small")
                query_vector = response.data[0].embedding
            except Exception as e:
                return f"Error creating embeddings: {e}"

            # --- 3. STRICT SQL QUERY ---
            sql_query = session.query(Exercise)

            # A. Zones & Forces (SQL IN)
            if zones_list:
                sql_query = sql_query.filter(Exercise.target_zone.in_(zones_list))
            if forces_list:
                sql_query = sql_query.filter(Exercise.force_type.in_(forces_list))

            # B. Safety (Cast to Array for Safety)
            if injuries_list:
                # We cast to ARRAY(VARCHAR) to ensure Postgres treats it as a list
                sql_query = sql_query.filter(
                    ~cast(Exercise.contraindications, ARRAY(VARCHAR)).op('&&')(cast(injuries_list, ARRAY(VARCHAR)))
                )

            # C. Equipment (The Fix)
            if equipment_list:
                # Explicitly CAST the column to ARRAY(VARCHAR) so the <@ operator works
                sql_query = sql_query.filter(
                    cast(Exercise.equipment, ARRAY(VARCHAR)).op('<@')(cast(equipment_list, ARRAY(VARCHAR)))
                )

            # --- 4. SEMANTIC RANKING ---
            sql_query = sql_query.order_by(Exercise.embedding.cosine_distance(query_vector))

            results = sql_query.limit(5).all()

            if not results:
                return (
                    f"No exercises found. Filters applied:\n"
                    f"- Zones: {zones_list}\n"
                    f"- Forces: {forces_list}\n"
                    f"- Equipment: {equipment_list}\n"
                )

            # --- 5. OUTPUT ---
            output_text = f"Found {len(results)} exercises:\n"
            for ex in results:
                output_text += f"NAME: {ex.name}\n"
                output_text += f"ZONE: {ex.target_zone} | TYPE: {ex.force_type}\n"
                output_text += f"EQUIPMENT: {', '.join(ex.equipment)}\n"
                output_text += f"INSTRUCTIONS: {ex.instructions[:100]}...\n"
                output_text += "---\n"
            
            return output_text

        except Exception as e:
            print(f"❌ CRITICAL TOOL ERROR: {str(e)}")
            return f"Database Error: {str(e)}"
        finally:
            session.close()