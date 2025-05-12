from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List


@CrewBase
class ExerciseSelector():
    """ExerciseSelector"""


    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def exercises_selector(self) -> Agent:
        return Agent(
            config=self.agents_config['exercises_selector'], 
            verbose=False
        )


    @task
    def select_exercises(self) -> Task:
        return Task(
            config=self.tasks_config['select_exercises'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the ExerciseSelector"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )