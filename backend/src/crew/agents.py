from crewai import Agent
from langchain_openai import ChatOpenAI
from src.crew.tools import ExerciseRetrieverTool

# Load the LLM (Brain)
# We use a specific temperature (0.2) to keep the agent creative but consistent.
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

class WorkoutAgents:
    def __init__(self):
        # We initialize the tool here so we can assign it to the Selector Agent
        self.exercise_tool = ExerciseRetrieverTool()

    def strategist_agent(self):
        return Agent(
            role='Senior Program Strategist',
            goal='Design the optimal weekly training structure (Split, Volume, Frequency) based on user bio-data.',
            backstory=(
                "You are a veteran strength coach with 20 years of experience. "
                "You do not care about specific exercises yet; you care about Volume, Frequency, and Splits. "
                "You decide if a user needs a Bro-Split, Upper/Lower, or Full Body based on their days available."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,     # Uses your specific GPT-4o config
            memory=True
        )

    def exercise_selector_agent(self):
        return Agent(
            role='Biomechanics Specialist',
            goal='Select the exact exercises that fit the user equipment and injury constraints using the database.',
            backstory=(
                "You are strict. You never invent exercises. You ONLY use your database tool. "
                "You take the Strategist's plan (e.g., 'Vertical Pull') and find the best match "
                "in the database (e.g., 'Pull Up' or 'Lat Pulldown')."
            ),
            verbose=True,
            allow_delegation=False,
            tools=[self.exercise_tool], # <--- Only this agent gets the Database Tool
            llm=llm,
            memory=True
        )

    def performance_coach_agent(self):
        return Agent(
            role='Performance Data Coach',
            goal='Assign Sets, Reps, Rest periods and Format the final output as strictly structured JSON.',
            backstory=(
                "You are a scientist. You analyze the user's goal (Hypertrophy vs Strength). "
                "If Hypertrophy: you assign 3-4 sets of 8-12 reps. "
                "If Strength: you assign 5 sets of 3-5 reps. "
                "You take the list of exercises and turn it into a structured JSON response "
                "that the application can save to the database."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm,
            memory=True
        )