"""
Robust code extraction and validation for AI-generated game code.

Replaces fragile regex-based cleaning with AST-based parsing and validation.
"""

import ast
import re
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of code extraction."""
    code: str
    success: bool
    method: str  # "structured", "fenced", "heuristic"
    warnings: List[str]


def extract_from_structured_output(output: str) -> ExtractionResult:
    """
    Extract code from structured output (JSON/Pydantic).

    Expects output to be a JSON object with a 'code' field.
    Tries to extract JSON from the beginning of the string.
    """
    import json

    stripped = output.strip()

    # Try to find a JSON object at the start of the string
    # Look for the first complete JSON object
    if not stripped.startswith('{'):
        return ExtractionResult(
            code="",
            success=False,
            method="structured",
            warnings=["Output does not start with JSON object"]
        )

    # Try to parse the whole thing first
    try:
        data = json.loads(stripped)
        if isinstance(data, dict) and 'code' in data:
            code = data['code']
            if isinstance(code, str) and code.strip():
                return ExtractionResult(
                    code=code.strip(),
                    success=True,
                    method="structured",
                    warnings=[]
                )
    except json.JSONDecodeError:
        # If whole string isn't valid JSON, try to extract first JSON object
        # Find matching braces
        brace_count = 0
        json_end = -1
        for i, char in enumerate(stripped):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break

        if json_end > 0:
            json_part = stripped[:json_end]
            try:
                data = json.loads(json_part)
                if isinstance(data, dict) and 'code' in data:
                    code = data['code']
                    if isinstance(code, str) and code.strip():
                        return ExtractionResult(
                            code=code.strip(),
                            success=True,
                            method="structured",
                            warnings=[]
                        )
            except json.JSONDecodeError:
                pass

    return ExtractionResult(
        code="",
        success=False,
        method="structured",
        warnings=["Output is not valid JSON with 'code' field"]
    )


def extract_from_fenced_blocks(text: str) -> ExtractionResult:
    """
    Extract code from markdown fenced code blocks.

    Handles ```python, ```py, ``` blocks.
    """
    # Find all fenced code blocks
    pattern = r'```(?:python|py)?\s*\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if matches:
        # Join all code blocks (in case there are multiple)
        code = "\n\n".join(matches)
        return ExtractionResult(
            code=code.strip(),
            success=True,
            method="fenced",
            warnings=[] if len(matches) == 1 else [f"Multiple code blocks found ({len(matches)}), joined together"]
        )

    return ExtractionResult(
        code="",
        success=False,
        method="fenced",
        warnings=["No fenced code blocks found"]
    )


def extract_heuristic(text: str) -> ExtractionResult:
    """
    Heuristic extraction for raw/unformatted output.

    Attempts to find Python code by looking for import statements
    and filtering out explanatory text.
    """
    warnings = []

    # Remove common explanation patterns
    explanation_patterns = [
        r'^#{1,6}\s+.*$',  # Markdown headers
        r'^\*\*.*\*\*\s*$',  # Bold lines
        r'^Here\s+(is|are)\s+.*$',
        r'^This\s+(code|game|script|program)\s+.*$',
        r'^The\s+(above|following|code|game)\s+.*$',
        r'^I\s+(have|created|made|wrote|built|generated)\s+.*$',
        r'^Below\s+is\s+.*$',
        r'^Note[:\s].*$',
        r'^Explanation[:\s].*$',
        r'^Output[:\s].*$',
        r'^Key\s+(features|changes|improvements)[:\s].*$',
        r'^\*\s+\*\*.*$',
        r'^\d+\.\s+\*\*.*$',
    ]

    cleaned = text
    for pattern in explanation_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

    # Remove stray backticks
    cleaned = re.sub(r'^```(?:python|py)?\s*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^```\s*$', '', cleaned, flags=re.MULTILINE)

    # Find first import/from/shebang line
    lines = cleaned.split('\n')
    code_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ', '#!')):
            code_start = i
            break

    if code_start > 0:
        lines = lines[code_start:]
        cleaned = '\n'.join(lines)
        warnings.append(f"Removed {code_start} lines of leading non-code text")
    elif code_start == -1:
        # No import statement found - check if there's any code-like content
        # If the entire cleaned text is just explanations, return failure
        non_empty_lines = [l for l in lines if l.strip()]
        if not non_empty_lines:
            return ExtractionResult(
                code="",
                success=False,
                method="heuristic",
                warnings=["Heuristic extraction produced empty code - only whitespace"]
            )
        # Check if any line looks like Python code
        has_code_like = False
        for l in non_empty_lines:
            stripped = l.strip()
            if stripped.startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'else',
                                 'elif ', 'for ', 'while ', 'try:', 'except', 'finally:',
                                 'with ', 'return ', 'yield ', 'raise ', 'pass', 'break',
                                 'continue', 'print(', 'self.', 'pygame.', '    ', '\t')):
                has_code_like = True
                break
            if stripped.endswith((':', ')', ']', '}', ',')):
                has_code_like = True
                break
            if '=' in stripped and not stripped.startswith('#'):
                has_code_like = True
                break

        if not has_code_like:
            return ExtractionResult(
                code="",
                success=False,
                method="heuristic",
                warnings=["No import statement found and no code-like content detected"]
            )

        warnings.append("No import statement found - using entire cleaned output")

    # Remove trailing non-code text
    lines = cleaned.split('\n')
    code_end = len(lines)

    # Look backwards for last line that looks like code
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check if line looks like Python code
        looks_like_code = any([
            stripped.startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'else',
                                 'elif ', 'for ', 'while ', 'try:', 'except', 'finally:',
                                 'with ', 'return ', 'yield ', 'raise ', 'pass', 'break',
                                 'continue', 'print(', 'self.', 'pygame.', '    ', '\t')),
            stripped.endswith((':', ')', ']', '}', ',')),
            '=' in stripped and not stripped.startswith('#'),
        ])

        if looks_like_code:
            code_end = i + 1
            break
        else:
            warnings.append(f"Removed trailing non-code line: {stripped[:50]}")

    cleaned = '\n'.join(lines[:code_end])

    # Normalize whitespace
    cleaned = re.sub(r'\n{4,}', '\n\n\n', cleaned)
    cleaned = cleaned.strip()

    if not cleaned:
        return ExtractionResult(
            code="",
            success=False,
            method="heuristic",
            warnings=["Heuristic extraction produced empty code"]
        )

    return ExtractionResult(
        code=cleaned,
        success=True,
        method="heuristic",
        warnings=warnings
    )


def extract_code(output: str) -> ExtractionResult:
    """
    Main extraction function - tries multiple strategies in order.

    Priority:
    1. Structured output (JSON with code field)
    2. Fenced code blocks
    3. Heuristic extraction
    """
    if not output or not output.strip():
        return ExtractionResult(
            code="",
            success=False,
            method="none",
            warnings=["Empty output"]
        )

    # Strategy 1: Structured output
    result = extract_from_structured_output(output)
    if result.success:
        logger.info(f"Code extracted via structured output: {len(result.code)} chars")
        return result

    # Strategy 2: Fenced blocks
    result = extract_from_fenced_blocks(output)
    if result.success:
        logger.info(f"Code extracted via fenced blocks: {len(result.code)} chars")
        return result

    # Strategy 3: Heuristic
    result = extract_heuristic(output)
    logger.info(f"Code extracted via heuristic: {len(result.code)} chars, warnings: {result.warnings}")
    return result


def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that code is syntactically correct Python.

    Returns:
        (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"


def validate_game_structure(code: str) -> Tuple[bool, List[str]]:
    """
    Validate that code has expected game structure.

    Returns:
        (is_valid, list_of_issues)
    """
    issues = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, ["Syntax error - cannot analyze structure"]

    # Check for required imports
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    required_imports = {'pygame'}
    missing_imports = required_imports - imports
    if missing_imports:
        issues.append(f"Missing required imports: {missing_imports}")

    # Check for pygame.init() call
    has_pygame_init = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'init':
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pygame':
                        has_pygame_init = True
                        break

    if not has_pygame_init:
        issues.append("Missing pygame.init() call")

    # Check for display creation
    has_display = False
    for node in ast.walk(tree):
        # Check for pygame.display.set_mode() call (possibly assigned to variable)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ('set_mode', 'set_caption'):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pygame':
                        has_display = True
                        break
                # Also check for pygame.display.set_mode assigned to variable
                if node.func.attr == 'set_mode':
                    if isinstance(node.func.value, ast.Attribute):
                        if node.func.value.attr == 'display':
                            if isinstance(node.func.value.value, ast.Name) and node.func.value.value.id == 'pygame':
                                has_display = True
                                break
        # Check for assignment: screen = pygame.display.set_mode(...)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Attribute):
                        if node.value.func.attr == 'set_mode':
                            if isinstance(node.value.func.value, ast.Attribute):
                                if node.value.func.value.attr == 'display':
                                    if isinstance(node.value.func.value.value, ast.Name) and node.value.func.value.value.id == 'pygame':
                                        has_display = True
                                        break
                if has_display:
                    break

    if not has_display:
        issues.append("Missing pygame.display.set_mode() call")

    # Check for game loop (while True or while running)
    has_loop = False
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_loop = True
                break
            if isinstance(node.test, ast.Name) and node.test.id in ('running', 'game_running'):
                has_loop = True
                break

    if not has_loop:
        issues.append("No main game loop found (while True or while running)")

    # Check for clock.tick()
    has_clock_tick = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'tick':
                    has_clock_tick = True
                    break

    if not has_clock_tick:
        issues.append("Missing clock.tick() for FPS control")

    # Check for pygame.quit()
    has_quit = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'quit':
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 'pygame':
                        has_quit = True
                        break

    if not has_quit:
        issues.append("Missing pygame.quit() call")

    # Check for main guard
    has_main = False
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if isinstance(node.test, ast.Compare):
                left = node.test.left
                if isinstance(left, ast.Name) and left.id == '__name__':
                    for comparator in node.test.comparators:
                        if isinstance(comparator, ast.Constant) and comparator.value == '__main__':
                            has_main = True
                            break

    if not has_main:
        issues.append("Missing if __name__ == '__main__': guard")

    return len(issues) == 0, issues


def validate_imports(code: str, allowed_imports: Optional[set] = None) -> Tuple[bool, List[str]]:
    """
    Validate that code only uses allowed imports.

    Returns:
        (is_valid, list_of_issues)
    """
    if allowed_imports is None:
        allowed_imports = {
            'pygame', 'random', 'sys', 'os', 'math', 'time', 'json',
            'typing', 'dataclasses', 'collections', 'itertools', 'functools',
            'subprocess'
        }

    issues = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, ["Syntax error - cannot analyze imports"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module not in allowed_imports:
                    issues.append(f"Disallowed import: {module}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split('.')[0]
                if module not in allowed_imports:
                    issues.append(f"Disallowed import: {module}")

    return len(issues) == 0, issues


def scan_ast_for_dangerous_patterns(code: str) -> List[str]:
    """
    Scan AST for potentially dangerous patterns.

    Returns:
        List of warning messages (empty if clean)
    """
    warnings = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return ["Syntax error - cannot scan for dangerous patterns"]

    dangerous_functions = {
        'os': ['system', 'popen', 'spawn', 'exec', 'fork', 'kill', 'remove', 'rmdir', 'unlink'],
        'subprocess': ['run', 'call', 'Popen', 'check_output', 'check_call'],
        'shutil': ['rmtree', 'move', 'copy', 'copy2', 'copytree', 'disk_usage'],
        'builtins': ['eval', 'exec', 'compile', '__import__'],
        'importlib': ['import_module', 'reload'],
        'socket': ['socket', 'connect', 'bind', 'listen', 'accept'],
        'urllib': ['urlopen', 'Request', 'urlretrieve'],
        'requests': ['get', 'post', 'put', 'delete', 'request'],
        'pathlib': ['Path', 'write_text', 'write_bytes', 'unlink', 'rmdir'],
    }

    dangerous_attributes = {
        'os': ['system', 'popen'],
        'subprocess': ['Popen'],
    }

    # Modules that are allowed to be imported but have dangerous functions
    # These should only trigger warnings on actual dangerous calls, not imports
    allowed_but_dangerous = {'os', 'subprocess', 'shutil', 'pathlib'}

    for node in ast.walk(tree):
        # Check for dangerous function calls
        if isinstance(node, ast.Call):
            # Check attribute calls like os.system()
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    module = node.func.value.id
                    func = node.func.attr
                    if module in dangerous_functions and func in dangerous_functions[module]:
                        warnings.append(f"Dangerous call detected: {module}.{func}() at line {node.lineno}")

            # Check direct calls like eval()
            elif isinstance(node.func, ast.Name):
                func = node.func.id
                if func in dangerous_functions.get('builtins', []):
                    warnings.append(f"Dangerous builtin call: {func}() at line {node.lineno}")

        # Check for dangerous imports (only for modules not in allowed_but_dangerous)
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                if module in dangerous_functions and module not in allowed_but_dangerous:
                    warnings.append(f"Potentially dangerous import: {module}")

        if isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split('.')[0]
                if module in dangerous_functions and module not in allowed_but_dangerous:
                    warnings.append(f"Potentially dangerous import: {module}")

    return warnings


def full_validation(code: str) -> Tuple[bool, List[str]]:
    """
    Run all validations on generated code.

    Returns:
        (is_valid, list_of_all_issues)
    """
    all_issues = []

    # Syntax check
    valid, error = validate_python_syntax(code)
    if not valid:
        all_issues.append(f"SYNTAX: {error}")
        return False, all_issues

    # Structure check
    valid, issues = validate_game_structure(code)
    if not valid:
        all_issues.extend([f"STRUCTURE: {i}" for i in issues])

    # Import check
    valid, issues = validate_imports(code)
    if not valid:
        all_issues.extend([f"IMPORT: {i}" for i in issues])

    # Security scan
    warnings = scan_ast_for_dangerous_patterns(code)
    if warnings:
        all_issues.extend([f"SECURITY: {w}" for w in warnings])

    return len(all_issues) == 0, all_issues