"""
Optimization Task for AI Game Studio.

Optimizes the pygame game code for performance, stability, and quality.
"""

from crewai import Task
from agents.optimizer import optimizer
from models.game_output import OptimizationTaskOutput

optimize_task = Task(
    description="""
    Optimize the pygame game code for performance, stability, and quality.

    OPTIMIZE:
    - FPS stability using pygame.time.Clock.tick(60) with delta-time
    - Memory: remove off-screen objects, limit list sizes
    - Code structure: clean organization, consistent naming
    - Visual polish: smooth animations using pygame.draw primitives only

    PRESERVE THESE (DO NOT REMOVE OR BREAK):
    - All gameplay mechanics (movement, enemies, scoring, game over, restart)
    - Increasing difficulty system
    - All collision detection logic

    AUDIO RULES (CRITICAL):
    - If audio code exists, ensure pygame.mixer.init() is wrapped in try/except
    - If no audio code exists, do NOT add any
    - The game must run with ZERO audio files present
    - Never add pygame.mixer.Sound() or pygame.mixer.music.load() calls

    ASSET RULES:
    - Do NOT add any pygame.image.load() calls
    - Do NOT add any external font file loads
    - Use ONLY pygame.font.Font(None, size) for text
    - Use ONLY pygame.draw for all graphics

    OUTPUT FORMAT (CRITICAL - FOLLOW EXACTLY):
    - Return ONLY the complete, clean, executable Python code
    - The first line must be an import statement
    - Do NOT include markdown formatting (no ```python``` blocks)
    - Do NOT include explanations, analysis, or comments outside the code
    - Do NOT include any text before or after the Python code
    - The output must be directly saveable as a .py file and runnable
    """,
    expected_output="Final optimized pygame code as clean executable Python only. No markdown, no explanations, no backticks.",
    agent=optimizer,
    output_pydantic=OptimizationTaskOutput,
)