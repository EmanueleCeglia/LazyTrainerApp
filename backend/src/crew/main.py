from crewai import Crew, Process
from src.crew.agents import WorkoutAgents
from src.crew.tasks import WorkoutTasks

class WorkoutCrew:
    def __init__(self, user_profile):
        self.user_profile = user_profile

    def run(self):
        # 1. Instantiate the Factory
        agents = WorkoutAgents()
        tasks = WorkoutTasks()

        # 2. Summon the Agents
        strategist = agents.strategist_agent()
        selector = agents.exercise_selector_agent()
        coach = agents.performance_coach_agent()

        # 3. Assign the Tasks
        # The output of strategy_task automatically becomes input for selection_task, etc.
        strategy_task = tasks.strategy_task(strategist, self.user_profile)
        selection_task = tasks.selection_task(selector, self.user_profile)
        coaching_task = tasks.coaching_task(coach, self.user_profile)

        # 4. Assemble the Crew (The Tribunal)
        crew = Crew(
            agents=[strategist, selector, coach],
            tasks=[strategy_task, selection_task, coaching_task],
            verbose=True,  # This will print the thought process of each agent to your console
            process=Process.sequential # Enforce strict order: Strategy -> Selection -> Coaching
        )

        # 5. Kickoff!
        result = crew.kickoff()
        return result