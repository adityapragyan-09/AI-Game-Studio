"""
Tests for generated game validation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.code_extraction import (
    validate_python_syntax,
    validate_game_structure,
    validate_imports,
    scan_ast_for_dangerous_patterns,
    full_validation
)


class TestValidationIntegration:
    """Integration tests for validation pipeline."""

    def test_valid_generated_game(self):
        """Test a typical valid generated game."""
        code = '''
import pygame
import random
import sys
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Test Game")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class Player:
    def __init__(self):
        self.x = 100
        self.y = 300
        self.rect = pygame.Rect(self.x, self.y, 50, 50)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= 5
        if keys[pygame.K_RIGHT]:
            self.x += 5
        self.rect.x = self.x

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

player = Player()
running = True

while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update()
    screen.fill(BLACK)
    player.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()

if __name__ == "__main__":
    pass
'''
        valid, issues = full_validation(code)
        assert valid is True, f"Valid game failed validation: {issues}"

    def test_game_with_audio_safety(self):
        """Test game with proper audio safety pattern."""
        code = '''
import pygame
import random
import sys

pygame.init()

AUDIO_ENABLED = False
try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
sys.exit()

if __name__ == "__main__":
    pass
'''
        valid, issues = full_validation(code)
        assert valid is True, f"Game with audio safety failed: {issues}"

    def test_game_with_dangerous_imports_fails(self):
        """Test that dangerous imports are caught."""
        code = '''
import pygame
import os
import subprocess

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

os.system("rm -rf /")

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
sys.exit()

if __name__ == "__main__":
    pass
'''
        valid, issues = full_validation(code)
        assert valid is False
        assert any("SECURITY" in i for i in issues)

    def test_game_with_eval_fails(self):
        """Test that eval/exec are caught."""
        code = '''
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

eval("__import__('os').system('ls')")

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
sys.exit()

if __name__ == "__main__":
    pass
'''
        valid, issues = full_validation(code)
        assert valid is False
        assert any("SECURITY" in i for i in issues)

    def test_minimal_game_structure(self):
        """Test minimal but complete game structure."""
        code = '''
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
sys.exit()

if __name__ == "__main__":
    pass
'''
        valid, issues = full_validation(code)
        assert valid is True, f"Minimal game failed: {issues}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])