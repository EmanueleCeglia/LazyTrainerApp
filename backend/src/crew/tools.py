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
            # --- 1. CLEAN INPUTS ---
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

            print(f"\n🔍 SEARCH: '{query}'")
            print(f"   Equip: {equipment_list} | Zone: {zones_list}")

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
            
            # The Critical Equipment Filter
            if equipment_list:
                sql_query = sql_query.filter(
                    cast(Exercise.equipment, ARRAY(VARCHAR)).op('<@')(cast(equipment_list, ARRAY(VARCHAR)))
                )

            sql_query = sql_query.order_by(Exercise.embedding.cosine_distance(query_vector))
            results = sql_query.limit(10).all() # Increased limit to ensure we get hits

            if not results:
                return "No exercises found matching criteria."

            # --- 4. FORMAT OUTPUT (WITH SANITIZER) ---
            output_text = f"Found {len(results)} exercises:\n"
            
            for ex in results:
                # 🛡️ THE SANITIZER: Check if equipment is broken (list of chars)
                # If ex.equipment looks like ['{', 'B', 'a', 'r'...], we fix it.
                equip_display = ex.equipment
                
                # Check for the "List of Chars" bug
                if isinstance(equip_display, list) and len(equip_display) > 0 and (equip_display[0] == '{' or len(equip_display[0]) == 1):
                     # Re-join characters: ['{', 'B', 'a', 'r', 'b', 'e', 'l', 'l', '}'] -> "{Barbell}"
                     raw_str = "".join(equip_display)
                     # Clean syntax: "{Barbell}" -> "Barbell"
                     clean_str = raw_str.replace('{', '').replace('}', '').replace('"', '')
                     # Split back to list: "Barbell,Bench" -> ["Barbell", "Bench"]
                     equip_display = clean_str.split(',')

                # Format nicely
                equip_str = ", ".join(equip_display) if isinstance(equip_display, list) else str(equip_display)

                output_text += f"NAME: {ex.name}\n"
                output_text += f"ZONE: {ex.target_zone} | TYPE: {ex.force_type}\n"
                output_text += f"EQUIPMENT: {equip_str}\n" # <--- Using sanitized string
                output_text += f"INSTRUCTIONS: {ex.instructions[:100]}...\n"
                output_text += "---\n"
            
            return output_text

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return f"Database Error: {str(e)}"
        finally:
            session.close()