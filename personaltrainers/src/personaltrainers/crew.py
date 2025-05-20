from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent, BaseModel
from crewai.tools import tool
from typing import List, Dict
from tools.db_call import db_call
import pandas as pd

class WhereClause(BaseModel):
    clause: str

class MacroExercises(BaseModel):
    exercises: str

class FinalExercises(BaseModel):
    exercises: List[str]

@tool("sql_query_tool")
def sql_query_tool(where_clause: str) -> dict:
    """Execute a SELECT * FROM exercises_view {where_clause}."""
    df_exercises = db_call(where_clause)
    return df_exercises.to_dict(orient="records")


@CrewBase
class PersonalTrainers():
    """PersonalTrainers"""


    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def sql_query_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_query_generator'], 
            verbose=True
        )
    
    @agent
    def sql_query_caller(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_query_caller'], 
            tools=[sql_query_tool],
            verbose=True
        )
    
    @agent
    def esercises_selector(self) -> Agent:
        return Agent(
            config=self.agents_config['esercises_selector'], 
            verbose=True
        )


    @task
    def fetch_exercises(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_exercises'],
            output_pydantic=WhereClause  
        )
    

    @task
    def run_query(self) -> Task:
        return Task(
            description=(
            "Call `sql_query_tool` with the following clause:\n"
            "{{tasks.fetch_exercises.pydantic.clause}}"
            ),
            expected_output="A dictionary with the selected exercises.",
            agent=self.sql_query_caller(),
            tools=[sql_query_tool],
            context=[self.fetch_exercises()],
            output_pydantic=MacroExercises
        )


    @task
    def select_exercises(self) -> Task:
        return Task(
            config=self.tasks_config['select_exercises'],
            context=[self.run_query()],
            output_pydantic=FinalExercises
        )


    @crew
    def crew(self) -> Crew:
        """Creates the PersonalTrainers"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
