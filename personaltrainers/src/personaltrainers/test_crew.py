# ⬛️ Notebook cell 1
import sys, pathlib

# add the project root so Python can see `personaltrainers/`
ROOT = pathlib.Path.cwd()          # change if you launch the notebook elsewhere
sys.path.append(str(ROOT))

# reload local modules each time you run the cell (handy while editing)
from crew import Personaltrainers
from tools.db_call import db_call


# ⬛️ Notebook cell 2
def run(client_request: str):
    inputs = {"user_request": client_request}
    result = Personaltrainers().crew().kickoff(inputs=inputs).raw
    result = result.replace("`", "")
    result = result.replace("\n", "")
    return " ".join(result.split())

# ⬛️ Notebook cell 3  – use it
sql_filter = run("Create an upper-body routine focusing on chest and triceps")
final_df   = db_call(sql_filter)

import pandas as pd
final_df.head()