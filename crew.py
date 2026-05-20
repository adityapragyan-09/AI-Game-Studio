from crewai import Crew, Process
from agents.designer import game_designer
from agents.developer import game_developer
from agents.qa import qa_engineer
from agents.optimizer import optimizer
from tasks.design_task import design_task
from tasks.develop_task import develop_task
from tasks.qa_task import qa_task
from tasks.optimize_task import optimize_task

crew = Crew(
    agents=[
        game_designer,
        game_developer,
        qa_engineer,
        optimizer
    ],
    tasks=[
        design_task,
        develop_task,
        qa_task,
        optimize_task
    ],
    process=Process.sequential,
    verbose=True
)