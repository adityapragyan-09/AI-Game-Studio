"""
QA Task for AI Game Studio.

Reviews and fixes the generated pygame game code. This is the FINAL stage before saving.
"""

from crewai import Task
from agents.qa import qa_engineer
from models.game_output import QATaskOutput

qa_task = Task(
    description="""
    Review and fix the generated pygame game code. This is the FINAL stage before saving.

    BUG CHECK:
    - Verify all variables are defined before use
    - Verify no NameError, TypeError, or AttributeError at runtime
    - Verify game loop runs without crashing
    - Verify collision detection works correctly
    - Verify scoring increments properly
    - Verify game over triggers correctly
    - Verify restart resets all state properly

    AUDIO SAFETY AUDIT (CRITICAL):
    - If pygame.mixer.init() exists, it MUST be wrapped in try/except
    - If ANY audio file loading exists (Sound, music.load), it MUST check os.path.exists() first
    - If safe audio helpers exist (play_sfx, play_music), verify they check for None
    - If NO audio code exists, do NOT add any — the game should work silently
    - The game MUST run perfectly with ZERO audio files on disk

    ASSET SAFETY AUDIT:
    - Verify NO pygame.image.load() calls exist
    - Verify NO external font file loads exist (only pygame.font.Font(None, size))
    - Verify ALL graphics use pygame.draw primitives only
    - Verify NO references to .png, .jpg, .wav, .mp3, .ogg files

    GAMEPLAY QUALITY CHECK:
    - Player can move in all intended directions
    - Enemies spawn and move correctly
    - Difficulty increases over time
    - Score is visible and updates
    - Game over screen shows final score
    - Restart works cleanly

    OUTPUT FORMAT (THIS IS THE MOST CRITICAL RULE):
    - Return ONLY the COMPLETE fixed Python code
    - First line MUST be an import statement (e.g., import pygame)
    - Do NOT wrap code in ```python``` or ``` blocks
    - Do NOT include ANY text before the first import
    - Do NOT include ANY text after the last line of code
    - Do NOT include explanations, summaries, or analysis
    - The output must be a valid .py file that runs with: python game.py
    """,
    expected_output="Complete fixed pygame game as raw executable Python code. No markdown, no backticks, no explanations.",
    agent=qa_engineer,
    output_pydantic=QATaskOutput,
)