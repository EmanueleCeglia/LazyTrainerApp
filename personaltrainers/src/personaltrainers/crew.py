from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pathlib import Path
import yaml
from tools.db_tool import TOOL_REGISTRY 

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

BASE = Path(__file__).resolve().parent 

def load_yaml(filename: str):
    with open(BASE / "config" / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@CrewBase
class Personaltrainers():
    """Personaltrainers crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = load_yaml("agents.yaml")
    tasks_config  = load_yaml("tasks.yaml")

    # helper che risolve i tools per un agente
    def _build_agent(self, key: str) -> Agent:
        cfg = dict(self.agents_config[key])   # copy so we can mutate
        aliases = cfg.pop("tools", [])        # ['pg_search_tool']
        tool_objs = [TOOL_REGISTRY[a] for a in aliases]
        return Agent(
            name=key,
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=tool_objs,
            verbose=True
        )

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def prompt_interpreter(self) -> Agent:
        return self._build_agent("prompt_interpreter")


    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def fetch_exercises(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_exercises'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Personaltrainers crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            #process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
