from crewai import Crew, Process
from src.crew.agents import WorkoutAgents
from src.crew.tasks import WorkoutTasks

class WorkoutCrew:
    def __init__(self, user_profile):
        self.user_profile = user_profile

    def run(self):
        # 1. Instantiate Agents & Tasks
        agents = WorkoutAgents()
        tasks = WorkoutTasks()

        coach = agents.biomechanics_coach()
        
        # 2. Create the specific task with user data
        design_plan = tasks.design_plan_task(
            agent=coach,
            user_profile=self.user_profile
        )

        # 3. Assemble the Crew
        crew = Crew(
            agents=[coach],
            tasks=[design_plan],
            verbose=True, # Logs the entire thinking process
            process=Process.sequential
        )

        # 4. Kickoff!
        result = crew.kickoff()
        return result