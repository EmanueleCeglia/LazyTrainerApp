

def prep_prompt_for_fetch_exercises(payload: dict) -> str:

    if payload.get('train_target') == 'Full body':
        payload['train_target'] = 'Upper body, Lower body'

    prompt = f"""
    Select the exercises using these informations:
    - body_region: {payload.get('train_target')}"""

    if payload.get('focus_muscle'):
        prompt += f""" 
        - muscles: {payload.get('muscles')}"""

    if payload.get('equipment'):
        prompt += f"""
        - equipment: {payload.get('equipment')}"""
        
    prompt = prompt.replace("'", "")
    prompt = prompt.replace("[", "")
    prompt = prompt.replace("]", "")
    
    return prompt