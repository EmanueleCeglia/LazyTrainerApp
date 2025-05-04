import os
from crew import Personaltrainers
from tools.db_call import db_call

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run(client_request: str):
    """
    Run the crew.
    """
    inputs = {
        'user_request': f'{client_request}'
    }
    
    # Create and run the crew
    result = Personaltrainers().crew().kickoff(inputs=inputs)

    return result.raw

if __name__ == "__main__":

    sql_filter = run()

    final_df = db_call(sql_filter)

    print(final_df)

