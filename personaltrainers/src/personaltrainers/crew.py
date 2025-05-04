from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List



@CrewBase
class Personaltrainers():
    """Personaltrainers crew"""


    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def prompt_interpreter(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_interpreter'], 
            verbose=True
        )


    @task
    def fetch_exercises(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_exercises'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Personaltrainers crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
