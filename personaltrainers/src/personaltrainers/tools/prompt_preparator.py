

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


def prep_prompt_for_select_exercises(payload: dict) -> str:

    prompt = f"The user, with {payload.get('level')} experience, is looking for a/an {payload.get('train_target')} training program focusing "

    if payload.get('focus_muscle'):
        prompt += f"on the following muscles: {payload.get('muscles')}. "
    else:
        prompt += f"on all the muscles presents in the selected exercises. "

    prompt += f"The duration of the training program is {payload.get('duration_minutes')} minutes"
    
    return prompt