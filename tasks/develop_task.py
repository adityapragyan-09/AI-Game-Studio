"""
Development Task for AI Game Studio.

Generates a complete playable pygame game based on the game concept provided.
"""

from crewai import Task
from agents.developer import game_developer
from models.game_output import DevelopmentTaskOutput

develop_task = Task(
    description="""
    Generate a complete playable pygame game based on the game concept provided.

    ABSOLUTE REQUIREMENTS - FOLLOW EXACTLY:
    1. Output ONLY raw Python code. No markdown. No explanations. No backticks. No commentary.
    2. The first line of output MUST be: import pygame
    3. Do NOT wrap code in ```python``` blocks
    4. Do NOT include any text before or after the Python code

    AUDIO RULES (CRITICAL - GAME WILL CRASH WITHOUT THESE):
    - Do NOT use pygame.mixer.init() directly. Instead wrap it:
        AUDIO_ENABLED = False
        try:
            pygame.mixer.init()
            AUDIO_ENABLED = True
        except Exception:
            AUDIO_ENABLED = False
    - Do NOT load any audio files (no .wav, .mp3, .ogg)
    - Do NOT call pygame.mixer.Sound() or pygame.mixer.music.load()
    - The game must work with ZERO audio files present

    ASSET RULES:
    - Do NOT use pygame.image.load() — no external images
    - Do NOT use pygame.font.Font("filename") — use pygame.font.Font(None, size) only
    - ALL graphics must use pygame.draw primitives (rect, circle, line, polygon)
    - Use color tuples for all visuals

    GAMEPLAY REQUIREMENTS:
    - Player movement with arrow keys
    - Enemy spawning and AI movement
    - Collision detection between player and enemies
    - Scoring system displayed on screen
    - Game over screen when player dies
    - Restart system (press R to restart)
    - Increasing difficulty over time (faster enemies, more spawns)
    - Smooth 60 FPS game loop with pygame.time.Clock

    CODE STRUCTURE:
    - import pygame, random, sys at the top
    - Constants section (colors, dimensions, speeds)
    - Game classes (Player, Enemy, etc.)
    - Main game loop with event handling, update, draw
    - if __name__ == "__main__": main()
    """,
    expected_output="Complete executable Python pygame game code. Raw Python only, no markdown, no explanations.",
    agent=game_developer,
    output_pydantic=DevelopmentTaskOutput,
)