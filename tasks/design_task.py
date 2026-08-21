"""
Design Task for AI Game Studio.

Creates a detailed game concept based on the user's game idea.
"""

from crewai import Task
from agents.designer import game_designer
from models.game_output import DesignTaskOutput

design_task = Task(
    description="""
    Create a detailed game concept for: {{game_idea}}

    Include:
    - Core gameplay mechanics and loop
    - Controls (keyboard-based, arrow keys + space)
    - Scoring system with increasing difficulty
    - Enemy types and behavior patterns
    - Progression system and difficulty scaling
    - Visual style description (ALL graphics must use pygame.draw primitives — NO external image files)

    IMPORTANT CONSTRAINTS:
    - The game MUST NOT require any external assets (no images, no sounds, no fonts)
    - All visuals must be achievable with pygame.draw (rectangles, circles, lines, polygons)
    - All text must use pygame.font.Font(None, size) — no custom font files
    - Do NOT design any audio/music/sound effects — the game will be completely silent
    - The game must be a single Python file using only pygame, random, sys, and os
    - Must include complete game loop with pygame.init(), display, clock, event handling
    - Must include restart functionality (press R to restart)
    - Must include game over state with final score display
    """,
    expected_output="Complete game design document with mechanics, controls, scoring, enemies, and visual style — all using pygame primitives only, no external assets.",
    agent=game_designer,
    output_pydantic=DesignTaskOutput,
)