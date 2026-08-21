"""
CrewAI crew configuration for AI Game Studio.

Orchestrates the multi-agent game generation pipeline.
"""

import logging
from crewai import Crew, Process

from agents.designer import game_designer
from agents.developer import game_developer
from agents.optimizer import optimizer
from agents.qa import qa_engineer
from tasks.design_task import design_task
from tasks.develop_task import develop_task
from tasks.qa_task import qa_task
from tasks.optimize_task import optimize_task

# Try to import LLM, handle missing config gracefully
try:
    from llm import llm, get_llm
    LLM_AVAILABLE = True
except (ValueError, ImportError) as e:
    logging.warning(f"LLM not available: {e}")
    LLM_AVAILABLE = False
    llm = None

logger = logging.getLogger(__name__)


def create_crew() -> Crew:
    """
    Create the game generation crew.

    Returns:
        Configured CrewAI Crew instance.

    Raises:
        ValueError: If LLM is not configured.
    """
    if not LLM_AVAILABLE or llm is None:
        # Try to initialize LLM now
        try:
            from llm import get_llm
            _llm = get_llm()
        except ValueError as e:
            raise ValueError(
                "Cannot create crew: Gemini API is not configured. "
                "Please set GEMINI_API_KEY environment variable."
            ) from e

    # Assign LLM to all agents
    for agent in [game_designer, game_developer, optimizer, qa_engineer]:
        agent.llm = llm

    crew = Crew(
        agents=[
            game_designer,
            game_developer,
            optimizer,
            qa_engineer
        ],
        tasks=[
            design_task,
            develop_task,
            optimize_task,
            qa_task
        ],
        process=Process.sequential,
        verbose=True
    )

    logger.info("Crew created successfully with 4 agents")
    return crew


# Create crew instance (lazy initialization)
_crew_instance = None


def get_crew() -> Crew:
    """Get or create the crew instance."""
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = create_crew()
    return _crew_instance


# Backward compatibility
try:
    crew = get_crew()
except ValueError:
    crew = None
    logger.warning("Crew initialization deferred - LLM not configured")