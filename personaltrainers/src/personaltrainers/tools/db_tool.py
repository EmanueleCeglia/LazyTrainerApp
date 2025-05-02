# tools/db_tool.py
from crewai_tools import PGSearchTool
from dotenv import load_dotenv
import os

load_dotenv()

# Read credentials from .env
db_tool = PGSearchTool(
    name="pg_search_tool",                       # <- alias referenced in YAML
    db_uri=(
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"@localhost:5432/"
        f"{os.getenv('POSTGRES_DB')}"
    ),
    table_name="exercise_full_view"              # the VIEW you just created
)

# Registry for the bootstrap
TOOL_REGISTRY = {"pg_search_tool": db_tool}

