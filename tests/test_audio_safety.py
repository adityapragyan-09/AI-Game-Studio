"""
Tests for audio safety AST transformations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.audio_safety import (
    AudioSafetyTransformer,
    apply_audio_safety,
    ensure_audio_safety_ast
)


class TestAudioSafety:
    """Tests for audio safety transformation."""

    def test_no_audio_init_unchanged(self):
        code = """
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))

while True:
    pass

pygame.quit()
"""
        result = ensure_audio_safety_ast(code)
        assert result == code

    def test_bare_audio_init_wrapped(self):
        code = """
import pygame
import sys

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((800, 600))

while True:
    pass

pygame.quit()
"""
        result = ensure_audio_safety_ast(code)
        assert "AUDIO_ENABLED = False" in result
        assert "try:" in result
        assert "except Exception:" in result
        assert "pygame.mixer.init()" in result

    def test_already_wrapped_unchanged(self):
        code = """
import pygame
import sys

AUDIO_ENABLED = False
try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False

pygame.init()
screen = pygame.display.set_mode((800, 600))

while True:
    pass

pygame.quit()
"""
        result = ensure_audio_safety_ast(code)
        # Should not double-wrap - original has 2 AUDIO_ENABLED = False (one at top, one in except)
        assert result.count("AUDIO_ENABLED = False") == 2
        assert result.count("try:") == 1
        # Should return essentially the same code
        assert "AUDIO_ENABLED = False" in result
        assert "try:" in result
        assert "except Exception:" in result

    def test_audio_init_with_other_mixer_calls(self):
        code = """
import pygame
import sys

pygame.init()
pygame.mixer.init()
sound = pygame.mixer.Sound("test.wav")
music = pygame.mixer.music.load("test.mp3")
screen = pygame.display.set_mode((800, 600))

while True:
    pass

pygame.quit()
"""
        result = ensure_audio_safety_ast(code)
        assert "AUDIO_ENABLED = False" in result
        assert "try:" in result

    def test_syntax_error_returns_original(self):
        code = """
import pygame
pygame.mixer.init(
# Missing closing paren
"""
        result = ensure_audio_safety_ast(code)
        assert result == code

    def test_multiple_audio_inits(self):
        code = """
import pygame
import sys

pygame.init()
pygame.mixer.init()
pygame.mixer.init()  # Duplicate
screen = pygame.display.set_mode((800, 600))

while True:
    pass

pygame.quit()
"""
        result = ensure_audio_safety_ast(code)
        # Both should be wrapped or at least one
        assert "try:" in result

    def test_apply_audio_safety_directly(self):
        code = """
import pygame
pygame.mixer.init()
"""
        result = apply_audio_safety(code)
        assert "AUDIO_ENABLED = False" in result
        assert "try:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])