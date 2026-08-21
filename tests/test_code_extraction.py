"""
Tests for code extraction and validation utilities.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.code_extraction import (
    extract_code,
    extract_from_structured_output,
    extract_from_fenced_blocks,
    extract_heuristic,
    validate_python_syntax,
    validate_game_structure,
    validate_imports,
    scan_ast_for_dangerous_patterns,
    full_validation,
    ExtractionResult
)


class TestStructuredOutputExtraction:
    """Tests for structured output extraction."""

    def test_valid_json_with_code(self):
        output = '{"code": "import pygame\\nprint(\\"hello\\")", "title": "Test"}'
        result = extract_from_structured_output(output)
        assert result.success is True
        assert result.method == "structured"
        assert "import pygame" in result.code

    def test_invalid_json(self):
        output = 'not json at all'
        result = extract_from_structured_output(output)
        assert result.success is False

    def test_json_without_code_field(self):
        output = '{"title": "Test"}'
        result = extract_from_structured_output(output)
        assert result.success is False

    def test_empty_code_field(self):
        output = '{"code": ""}'
        result = extract_from_structured_output(output)
        assert result.success is False


class TestFencedBlockExtraction:
    """Tests for fenced code block extraction."""

    def test_python_fenced_block(self):
        output = "Here is the code:\n```python\nimport pygame\nprint('hello')\n```"
        result = extract_from_fenced_blocks(output)
        assert result.success is True
        assert result.method == "fenced"
        assert "import pygame" in result.code

    def test_py_fenced_block(self):
        output = "```py\nimport pygame\n```"
        result = extract_from_fenced_blocks(output)
        assert result.success is True

    def test_plain_fenced_block(self):
        output = "```\nimport pygame\n```"
        result = extract_from_fenced_blocks(output)
        assert result.success is True

    def test_multiple_fenced_blocks(self):
        output = "```python\nimport pygame\n```\n\n```python\nprint('hello')\n```"
        result = extract_from_fenced_blocks(output)
        assert result.success is True
        assert "import pygame" in result.code
        assert "print('hello')" in result.code
        assert len(result.warnings) > 0

    def test_no_fenced_blocks(self):
        output = "import pygame\nprint('hello')"
        result = extract_from_fenced_blocks(output)
        assert result.success is False


class TestHeuristicExtraction:
    """Tests for heuristic extraction."""

    def test_raw_python_code(self):
        output = "import pygame\nimport random\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()"
        result = extract_heuristic(output)
        assert result.success is True
        assert result.method == "heuristic"
        assert result.code == output.strip()

    def test_code_with_explanation_before(self):
        output = "Here is the game code:\n\nimport pygame\nprint('hello')"
        result = extract_heuristic(output)
        assert result.success is True
        assert result.code.startswith("import pygame")

    def test_code_with_explanation_after(self):
        output = "import pygame\nprint('hello')\n\nThis code creates a game."
        result = extract_heuristic(output)
        assert result.success is True
        assert result.code == "import pygame\nprint('hello')"

    def test_code_with_markdown_headers(self):
        output = "# Game Code\n\nimport pygame\n\n## Features\n- Feature 1\n\nprint('hello')"
        result = extract_heuristic(output)
        assert result.success is True
        assert "import pygame" in result.code
        assert "print('hello')" in result.code

    def test_only_explanation_no_code(self):
        output = "This is just an explanation with no code."
        result = extract_heuristic(output)
        assert result.success is False


class TestMainExtraction:
    """Tests for main extract_code function."""

    def test_priority_structured_over_fenced(self):
        # Structured should win even if fenced blocks exist
        # Use valid JSON with escaped newline
        import json
        structured_part = json.dumps({"code": "import pygame\n# structured"})
        output = structured_part + "\n\n```python\nimport pygame\n# fenced\n```"
        result = extract_code(output)
        assert result.success is True
        assert result.method == "structured"
        assert "# structured" in result.code

    def test_priority_fenced_over_heuristic(self):
        output = "```python\nimport pygame\n# fenced\n```\n\nimport pygame\n# heuristic"
        result = extract_code(output)
        assert result.success is True
        assert result.method == "fenced"
        assert "# fenced" in result.code


class TestSyntaxValidation:
    """Tests for Python syntax validation."""

    def test_valid_syntax(self):
        code = "import pygame\nprint('hello')"
        valid, error = validate_python_syntax(code)
        assert valid is True
        assert error is None

    def test_invalid_syntax(self):
        code = "import pygame\nprint('hello'"  # Missing closing paren
        valid, error = validate_python_syntax(code)
        assert valid is False
        assert error is not None
        assert "Syntax error" in error

    def test_empty_code(self):
        code = ""
        valid, error = validate_python_syntax(code)
        # Empty string is valid Python (empty module)
        assert valid is True
        assert error is None


class TestGameStructureValidation:
    """Tests for game structure validation."""

    def test_valid_game_structure(self):
        code = """
import pygame
import random
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Test")
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
"""
        valid, issues = validate_game_structure(code)
        assert valid is True, f"Issues: {issues}"

    def test_missing_pygame_import(self):
        code = """
import random
import sys

pygame.init()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("Missing required imports" in i for i in issues)

    def test_missing_pygame_init(self):
        code = """
import pygame
import sys

screen = pygame.display.set_mode((800, 600))
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("pygame.init()" in i for i in issues)

    def test_missing_display(self):
        code = """
import pygame
import sys

pygame.init()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("display.set_mode" in i for i in issues)

    def test_missing_game_loop(self):
        code = """
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.quit()
sys.exit()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("game loop" in i for i in issues)

    def test_missing_clock_tick(self):
        code = """
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

while True:
    pass

pygame.quit()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("clock.tick" in i for i in issues)

    def test_missing_pygame_quit(self):
        code = """
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("pygame.quit" in i for i in issues)

    def test_missing_main_guard(self):
        code = """
import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

def main():
    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

main()
pygame.quit()
sys.exit()
"""
        valid, issues = validate_game_structure(code)
        assert valid is False
        assert any("__main__" in i for i in issues)


class TestImportValidation:
    """Tests for import validation."""

    def test_allowed_imports(self):
        code = "import pygame\nimport random\nimport sys\nimport math"
        valid, issues = validate_imports(code)
        assert valid is True

    def test_disallowed_import(self):
        code = "import pygame\nimport shutil\nimport os"
        valid, issues = validate_imports(code)
        assert valid is False
        assert any("shutil" in i for i in issues)

    def test_disallowed_from_import(self):
        code = "import pygame\nfrom shutil import rmtree"
        valid, issues = validate_imports(code)
        assert valid is False
        assert any("shutil" in i for i in issues)


class TestSecurityScan:
    """Tests for AST security scanning."""

    def test_eval_detection(self):
        code = "import pygame\nx = eval('1+1')"
        warnings = scan_ast_for_dangerous_patterns(code)
        assert len(warnings) > 0
        assert any("eval" in w for w in warnings)

    def test_exec_detection(self):
        code = "import pygame\nexec('print(1)')"
        warnings = scan_ast_for_dangerous_patterns(code)
        assert len(warnings) > 0
        assert any("exec" in w for w in warnings)

    def test_os_system_detection(self):
        code = "import pygame\nimport os\nos.system('ls')"
        warnings = scan_ast_for_dangerous_patterns(code)
        assert len(warnings) > 0
        assert any("os.system" in w for w in warnings)

    def test_subprocess_detection(self):
        code = "import pygame\nimport subprocess\nsubprocess.run(['ls'])"
        warnings = scan_ast_for_dangerous_patterns(code)
        assert len(warnings) > 0
        assert any("subprocess" in w for w in warnings)

    def test_safe_code_no_warnings(self):
        code = "import pygame\nimport random\nimport math\nprint('hello')"
        warnings = scan_ast_for_dangerous_patterns(code)
        assert len(warnings) == 0


class TestFullValidation:
    """Tests for full validation pipeline."""

    def test_fully_valid_code(self):
        code = """
import pygame
import random
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Test")
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
"""
        valid, issues = full_validation(code)
        assert valid is True, f"Issues: {issues}"

    def test_code_with_security_issue(self):
        code = """
import pygame
import os
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

os.system('rm -rf /')

while True:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    pass
"""
        valid, issues = full_validation(code)
        assert valid is False
        assert any("SECURITY" in i for i in issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])