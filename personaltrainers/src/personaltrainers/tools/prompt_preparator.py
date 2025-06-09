
from pydantic import BaseModel
from typing import Union

def prep_prompt_for_fetch_exercises(payload_orig) -> str:
    # Converti l'oggetto Pydantic in dizionario
    if hasattr(payload_orig, 'model_dump'):
        # Pydantic v2
        payload = payload_orig.model_dump()
    elif hasattr(payload_orig, 'dict'):
        # Pydantic v1
        payload = payload_orig.dict()
    else:
        # Se è già un dizionario
        payload = payload_orig.copy()
    
    # Modifica la copia del dizionario
    if payload['train_target'] == 'Full body':
        payload['train_target'] = 'Upper body, Lower body'

    prompt = f"""
    Select the exercises using these informations:
    - body_region: {payload['train_target']}"""

    if payload['focus_muscle']:
        prompt += f""" 
        - muscles: {payload['muscles']}"""

    if payload.get('equipment'):  # Usa .get() sul dizionario
        prompt += f"""
        - equipment: {payload['equipment']}"""
        
    prompt = prompt.replace("'", "")
    prompt = prompt.replace("[", "")
    prompt = prompt.replace("]", "")
    
    return prompt


def prep_prompt_for_select_exercises(payload) -> str:
    # Converti l'oggetto Pydantic in dizionario se necessario
    if hasattr(payload, 'model_dump'):
        # Pydantic v2
        data = payload.model_dump()
    elif hasattr(payload, 'dict'):
        # Pydantic v1
        data = payload.dict()
    else:
        # Se è già un dizionario
        data = payload

    prompt = f"The user, with {data['level']} experience, is looking for a/an {data['train_target']} training program focusing "

    if data['focus_muscle']:
        prompt += f"on the following muscles: {data['muscles']}. "
    else:
        prompt += f"on all the muscles presents in the selected exercises. "

    prompt += f"The duration of the training program is {data['duration_minutes']} minutes"
    
    return prompt


def prep_prompt_for_generate_protocols(payload) -> str:
    # Converti l'oggetto Pydantic in dizionario se necessario
    if hasattr(payload, 'model_dump'):
        # Pydantic v2
        data = payload.model_dump()
    elif hasattr(payload, 'dict'):
        # Pydantic v1
        data = payload.dict()
    else:
        # Se è già un dizionario
        data = payload

    user_level = data['level']
    # TODO: add workout goals like: increase mass, increase strenght etc for a more precise protocol generation
    
    return user_level