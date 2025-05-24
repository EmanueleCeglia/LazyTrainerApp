import sys, pathlib
from pathlib import Path
import json
import ast
import pandas as pd

from .crew import PersonalTrainers

from .tools.prompt_cache import cached_call
from .tools.prompt_preparator import prep_prompt_for_fetch_exercises, prep_prompt_for_select_exercises

ROOT = pathlib.Path.cwd()          
sys.path.append(str(ROOT))


def crew_pt(client_request: str, client_request_2 : str) -> str:
    inputs = {"user_request": client_request,
              "user_needs": client_request_2}
    result = PersonalTrainers().crew().kickoff(inputs=inputs).raw

    return result

def test_crew(payload):

    prompt_1 = prep_prompt_for_fetch_exercises(payload_orig=payload)

    prompt_2 = prep_prompt_for_select_exercises(payload=payload)

    # Call CREW with cached call
    filter_generated = cached_call(prompt_1, prompt_2, crew_pt)

    return filter_generated
