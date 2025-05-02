#!/usr/bin/env python
import sys
import warnings

from crew import Personaltrainers

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run(client_request: str):
    """
    Run the crew.
    """
    inputs = {
        'user_request': f'{client_request}'
    }
    
    try:
        Personaltrainers().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<client_request>\"")
        sys.exit(1)

    run(sys.argv[1])