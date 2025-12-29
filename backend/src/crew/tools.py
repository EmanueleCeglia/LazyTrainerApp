import os
from typing import List, Union, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
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
    description: str = "Search for exercises using strict SQL filtering."
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

            raw_equipment = parse_list(available_equipment)
            injuries_list = parse_list(user_injuries)
            zones_list = parse_list(target_zone)
            forces_list = parse_list(force_type)

            # --- 🛡️ BASIC NORMALIZATION ONLY ---
            # We trust the App to send correct names (e.g., "Dumbbell"), but we ensure Title Case for DB matching.
            final_equipment = [item.title() for item in raw_equipment]
            
            # Auto-add "Bodyweight" because user bodies are always available.
            # This ensures exercises like "Lunges" (requiring Dumbbell + Bodyweight) don't get filtered out.
            if "Bodyweight" not in final_equipment:
                final_equipment.append("Bodyweight")

            print(f"\n🔍 SEARCH: '{query}'")
            print(f"   User Has: {final_equipment}")
            print(f"   Filters: Zone={zones_list} | Force={forces_list}")

            # --- 2. EMBEDDINGS ---
            response = client.embeddings.create(input=query, model="text-embedding-3-small")
            query_vector = response.data[0].embedding

            # --- 3. BUILD QUERY ---
            sql_query = session.query(Exercise)

            if zones_list:
                sql_query = sql_query.filter(Exercise.target_zone.in_(zones_list))
            if forces_list:
                sql_query = sql_query.filter(Exercise.force_type.in_(forces_list))
            if injuries_list:
                sql_query = sql_query.filter(~cast(Exercise.contraindications, ARRAY(VARCHAR)).op('&&')(cast(injuries_list, ARRAY(VARCHAR))))
            
            # --- CRITICAL FILTER: SUBSET LOGIC ---
            # Logic: "Is the Exercise's required equipment a SUBSET of what the User has?"
            # Example: 
            #   User: [Dumbbell, Barbell, Bodyweight]
            #   Ex1: [Dumbbell] -> PASS
            #   Ex2: [Barbell] -> PASS
            #   Ex3: [Dumbbell, Barbell] -> PASS
            #   Ex4: [Cable] -> FAIL
            if final_equipment:
                sql_query = sql_query.filter(
                    cast(Exercise.equipment, ARRAY(VARCHAR)).op('<@')(cast(final_equipment, ARRAY(VARCHAR)))
                )

            sql_query = sql_query.order_by(Exercise.embedding.cosine_distance(query_vector))
            results = sql_query.limit(10).all()

            if not results:
                return (
                    f"No exercises found. \n"
                    f"User Equipment: {final_equipment}\n"
                    f"Filters: Zone={zones_list}, Force={forces_list}"
                )

            # --- 4. FORMAT OUTPUT ---
            output_text = f"Found {len(results)} exercises:\n"
            
            for ex in results:
                # 🛡️ Sanitizer for "List of Chars" bug (Safety net)
                equip_display = ex.equipment
                if isinstance(equip_display, list) and len(equip_display) > 0 and (equip_display[0] == '{' or len(equip_display[0]) == 1):
                     raw_str = "".join(equip_display)
                     clean_str = raw_str.replace('{', '').replace('}', '').replace('"', '')
                     equip_display = clean_str.split(',')

                equip_str = ", ".join(equip_display) if isinstance(equip_display, list) else str(equip_display)

                output_text += f"NAME: {ex.name}\n"
                output_text += f"ZONE: {ex.target_zone} | TYPE: {ex.force_type}\n"
                output_text += f"EQUIPMENT: {equip_str}\n"
                output_text += f"INSTRUCTIONS: {ex.instructions[:100]}...\n"
                output_text += "---\n"
            
            return output_text

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return f"Database Error: {str(e)}"
        finally:
            session.close()