from crewai import Agent
from langchain_openai import ChatOpenAI
from src.crew.tools import ExerciseRetrieverTool

# Load the LLM (Brain)
# We use a specific temperature (0.2) to keep the agent creative but consistent.
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

class WorkoutAgents:
    def biomechanics_coach(self):
        return Agent(
            role='Senior Biomechanics Coach',
            goal='Design safe, science-based workout programs using ONLY the exercises available in the database.',
            backstory=(
                "You are an elite Personal Trainer with a PhD in Biomechanics. "
                "You despise 'bro-science'. You only prescribe exercises that match the user's "
                "equipment and injury history. You strictly use your tools to find exercises; "
                "you never guess or invent exercise names."
            ),
            tools=[ExerciseRetrieverTool()], # Give him the "Sword" we created
            verbose=True, # Logs thoughts to console (Great for debugging)
            memory=True,
            llm=llm,
            allow_delegation=False
        )