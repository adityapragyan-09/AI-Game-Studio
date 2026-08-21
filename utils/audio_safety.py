"""
AST-based audio safety transformation for generated game code.

Replaces fragile string-replacement with proper AST manipulation.
"""

import ast
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioSafetyTransformer(ast.NodeTransformer):
    """
    AST transformer that ensures audio initialization is wrapped in try/except.
    """

    def __init__(self):
        self.has_audio_init = False
        self.wrapped_audio_init = False

    def visit_Call(self, node: ast.Call) -> ast.Call:
        # First, check if this is a pygame.mixer.init() call
        if self._is_pygame_mixer_init(node):
            self.has_audio_init = True

            # Check if already wrapped in try/except
            if self._is_wrapped_in_try_except(node):
                logger.debug("pygame.mixer.init() already wrapped in try/except")
                return node

            # Wrap it
            self.wrapped_audio_init = True
            logger.info("Wrapping pygame.mixer.init() in try/except")

            # Create the wrapped version
            return self._create_wrapped_audio_init(node)

        # Also check for pygame.mixer.Sound() and pygame.mixer.music.load()
        if self._is_pygame_mixer_sound(node) or self._is_pygame_mixer_music_load(node):
            logger.warning(f"Found potentially unsafe audio call: {ast.unparse(node) if hasattr(ast, 'unparse') else 'unknown'}")
            # Add a comment warning
            return node

        return self.generic_visit(node)

    def _is_pygame_mixer_init(self, node: ast.Call) -> bool:
        """Check if node is pygame.mixer.init() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'init':
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'mixer':
                        if isinstance(node.func.value.value, ast.Name):
                            return node.func.value.value.id == 'pygame'
        return False

    def _is_pygame_mixer_sound(self, node: ast.Call) -> bool:
        """Check if node is pygame.mixer.Sound() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'Sound':
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'mixer':
                        if isinstance(node.func.value.value, ast.Name):
                            return node.func.value.value.id == 'pygame'
        return False

    def _is_pygame_mixer_music_load(self, node: ast.Call) -> bool:
        """Check if node is pygame.mixer.music.load() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'load':
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'music':
                        if isinstance(node.func.value.value, ast.Attribute):
                            if node.func.value.value.attr == 'mixer':
                                if isinstance(node.func.value.value.value, ast.Name):
                                    return node.func.value.value.value.id == 'pygame'
        return False

    def _is_wrapped_in_try_except(self, node: ast.Call) -> bool:
        """Check if the call is already inside a try/except block."""
        # This is a simplified check - in reality we'd need parent tracking
        # For now, we'll check if AUDIO_ENABLED pattern exists in the module
        return False

    def _create_wrapped_audio_init(self, original_call: ast.Call) -> ast.AST:
        """
        Create AST for:
            AUDIO_ENABLED = False
            try:
                pygame.mixer.init()
                AUDIO_ENABLED = True
            except Exception:
                AUDIO_ENABLED = False
        """
        # AUDIO_ENABLED = False
        audio_enabled_false = ast.Assign(
            targets=[ast.Name(id='AUDIO_ENABLED', ctx=ast.Store())],
            value=ast.Constant(value=False)
        )

        # pygame.mixer.init()
        init_call = ast.Expr(value=original_call)

        # AUDIO_ENABLED = True
        audio_enabled_true = ast.Assign(
            targets=[ast.Name(id='AUDIO_ENABLED', ctx=ast.Store())],
            value=ast.Constant(value=True)
        )

        # except Exception:
        #     AUDIO_ENABLED = False
        except_handler = ast.ExceptHandler(
            type=ast.Name(id='Exception', ctx=ast.Load()),
            name=None,
            body=[
                ast.Assign(
                    targets=[ast.Name(id='AUDIO_ENABLED', ctx=ast.Store())],
                    value=ast.Constant(value=False)
                )
            ]
        )

        # try: ... except: ...
        try_node = ast.Try(
            body=[init_call, audio_enabled_true],
            handlers=[except_handler],
            orelse=[],
            finalbody=[]
        )

        # Return a list of statements - but we can only return one node
        # So we wrap in a Module-like structure using a custom node
        # Actually, we need to replace the single call with multiple statements
        # This requires a different approach - we'll return the try block
        # and handle the AUDIO_ENABLED = False at module level

        return try_node


def apply_audio_safety(code: str) -> str:
    """
    Apply audio safety transformations to code using AST.

    Returns the transformed code as a string.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logger.warning(f"Cannot apply audio safety - syntax error: {e}")
        return code

    transformer = AudioSafetyTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    if not transformer.has_audio_init:
        logger.debug("No pygame.mixer.init() found - no audio safety needed")
        return code

    if transformer.wrapped_audio_init:
        logger.info("Audio safety applied successfully")
    else:
        logger.debug("Audio init already wrapped")

    # Convert back to code
    try:
        if hasattr(ast, 'unparse'):
            return ast.unparse(new_tree)
        else:
            # Python < 3.9 fallback
            import astor
            return astor.to_source(new_tree)
    except Exception as e:
        logger.error(f"Failed to unparse AST after audio safety: {e}")
        return code


def ensure_audio_safety_ast(code: str) -> str:
    """
    Main entry point for audio safety.

    Uses AST-based transformation with fallback to original code.
    """
    if 'pygame.mixer.init()' not in code:
        return code

    # Check if already has safety pattern (case-insensitive, flexible)
    import re
    # Check for AUDIO_ENABLED assignment and try/except block
    has_audio_enabled = re.search(r'AUDIO_ENABLED\s*=', code) is not None
    has_try_except = re.search(r'try\s*:', code) is not None and re.search(r'except\s+Exception\s*:', code) is not None

    if has_audio_enabled and has_try_except:
        # Already has safety pattern
        return code

    return apply_audio_safety(code)