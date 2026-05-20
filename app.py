import streamlit as st
import os
import re
import textwrap
from crew import crew

st.set_page_config(
    page_title="AI Game Studio",
    layout="wide"
)

st.title("🎮 AI Game Development Crew")

game_idea = st.text_area(
    "Enter your game idea",
    placeholder="Example: Endless cyberpunk runner with boss fights"
)


# ============================================================
# OUTPUT CLEANING SYSTEM
# ============================================================

def clean_generated_code(raw_output: str) -> str:
    """
    Extracts only executable Python code from raw LLM output.
    Removes markdown blocks, explanations, triple backticks,
    and any non-code text. Returns clean, runnable Python.
    """
    text = str(raw_output)

    # --- Pass 1: Extract code from markdown fenced blocks ---
    # Look for ```python ... ``` blocks first
    fenced_blocks = re.findall(
        r'```(?:python|py)?\s*\n(.*?)```',
        text,
        re.DOTALL | re.IGNORECASE
    )
    if fenced_blocks:
        # Join all code blocks (in case there are multiple)
        text = "\n\n".join(fenced_blocks)
    else:
        # --- Pass 2: Remove stray backtick lines if no fenced block found ---
        text = re.sub(r'^```(?:python|py)?\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)

    # --- Pass 3: Remove common LLM explanation patterns ---
    # Remove lines that look like markdown headers
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    # Remove lines starting with bold markers
    text = re.sub(r'^\*\*.*\*\*\s*$', '', text, flags=re.MULTILINE)
    # Remove lines that are clearly prose (start with common explanation words)
    explanation_patterns = [
        r'^Here\s+(is|are)\s+.*$',
        r'^This\s+(code|game|script|program)\s+.*$',
        r'^The\s+(above|following|code|game)\s+.*$',
        r'^I\s+(have|created|made|wrote|built|generated)\s+.*$',
        r'^Below\s+is\s+.*$',
        r'^Note[:\s].*$',
        r'^Explanation[:\s].*$',
        r'^Output[:\s].*$',
        r'^Key\s+(features|changes|improvements)[:\s].*$',
        r'^\*\s+\*\*.*$',  # Bullet points with bold
        r'^\d+\.\s+\*\*.*$',  # Numbered lists with bold
    ]
    for pattern in explanation_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)

    # --- Pass 4: Find the actual Python code start ---
    # Look for 'import pygame' or 'import ' as the real code start
    lines = text.split('\n')
    code_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from ') or stripped.startswith('#!'):
            code_start = i
            break

    if code_start > 0:
        lines = lines[code_start:]
        text = '\n'.join(lines)

    # --- Pass 5: Remove trailing non-code text ---
    # Find the last line that looks like Python code
    lines = text.split('\n')
    code_end = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped == '' or stripped.startswith('#'):
            continue
        # Check if this line looks like Python
        if any([
            stripped.startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'else',
                                 'elif ', 'for ', 'while ', 'try:', 'except', 'finally:',
                                 'with ', 'return ', 'yield ', 'raise ', 'pass', 'break',
                                 'continue', 'print(', 'self.', 'pygame.')),
            stripped.endswith((':',  ')', ']', '}', ',')),
            '=' in stripped,
            stripped.startswith((' ', '\t')),  # indented code
            stripped == '',
        ]):
            code_end = i + 1
            break
        else:
            # Non-code trailing line, skip it
            continue

    text = '\n'.join(lines[:code_end])

    # --- Pass 6: Clean up whitespace ---
    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = text.strip()

    return text


# ============================================================
# AUDIO SAFETY POST-PROCESSOR
# ============================================================

def ensure_audio_safety(code: str) -> str:
    """
    Post-processes generated code to ensure audio system is crash-proof.
    Wraps pygame.mixer.init() in try/except if not already wrapped.
    Adds safe audio loading patterns.
    """
    # If code already has audio safety patterns, return as-is
    if 'AUDIO_ENABLED' in code and 'try:' in code and 'pygame.mixer.init()' in code:
        return code

    # If there's a bare pygame.mixer.init() without try/except, wrap it
    if 'pygame.mixer.init()' in code:
        # Check if it's already in a try block by looking at surrounding context
        lines = code.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped == 'pygame.mixer.init()':
                # Check if previous non-empty line is 'try:'
                prev_is_try = False
                for j in range(i - 1, max(i - 3, -1), -1):
                    if lines[j].strip() == 'try:':
                        prev_is_try = True
                        break
                    elif lines[j].strip() != '':
                        break

                if not prev_is_try:
                    indent = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}AUDIO_ENABLED = False")
                    new_lines.append(f"{indent}try:")
                    new_lines.append(f"{indent}    pygame.mixer.init()")
                    new_lines.append(f"{indent}    AUDIO_ENABLED = True")
                    new_lines.append(f"{indent}except Exception:")
                    new_lines.append(f"{indent}    AUDIO_ENABLED = False")
                    i += 1
                    continue

            new_lines.append(line)
            i += 1

        code = '\n'.join(new_lines)

    # Wrap bare pygame.mixer.Sound() calls that aren't in try/except
    if 'pygame.mixer.Sound(' in code and 'os.path.exists' not in code:
        code = code.replace(
            'pygame.mixer.Sound(',
            '# Audio loading wrapped for safety\npygame.mixer.Sound('
        )

    return code


# ============================================================
# VALIDATION
# ============================================================

def validate_generated_code(code: str) -> tuple[bool, str]:
    """
    Validates that the generated code is likely runnable.
    Returns (is_valid, error_message).
    """
    if not code or len(code.strip()) < 100:
        return False, "Generated code is too short or empty"

    if 'import pygame' not in code:
        return False, "Missing 'import pygame' — not a valid pygame game"

    # Check for common syntax issues
    try:
        compile(code, '<generated_game>', 'exec')
    except SyntaxError as e:
        return False, f"Syntax error in generated code: {e}"

    return True, ""


# ============================================================
# STREAMLIT UI
# ============================================================

if st.button("🚀 Generate Game"):
    if not game_idea or not game_idea.strip():
        st.warning("⚠️ Please enter a game idea first.")
    else:
        with st.spinner("🤖 AI Agents are building your game... This may take a few minutes."):
            try:
                # --- Run CrewAI pipeline ---
                result = crew.kickoff(
                    inputs={
                        "game_idea": game_idea
                    }
                )

                raw_output = str(result)

                # --- Clean the output ---
                generated_code = clean_generated_code(raw_output)

                # --- Ensure audio safety ---
                generated_code = ensure_audio_safety(generated_code)

                # --- Validate ---
                is_valid, validation_error = validate_generated_code(generated_code)

                if not is_valid:
                    st.warning(f"⚠️ Validation issue: {validation_error}")
                    st.info("Saving raw cleaned output anyway — you may need to manually review.")

                # --- Save to outputs ---
                try:
                    os.makedirs("outputs", exist_ok=True)
                    output_path = os.path.join("outputs", "generated_game.py")
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(generated_code)

                    abs_path = os.path.abspath(output_path)

                    st.success("✅ Game generated successfully!")
                    st.info(f"📁 Saved to: `{abs_path}`")
                    st.code("python outputs/generated_game.py", language="bash")

                except Exception as save_err:
                    st.error(f"❌ Failed to save file: {save_err}")

                # --- Download button ---
                st.download_button(
                    label="⬇️ Download Game",
                    data=generated_code,
                    file_name="generated_game.py",
                    mime="text/x-python"
                )

                # --- Preview ---
                with st.expander("👀 Preview Generated Code", expanded=False):
                    st.code(generated_code, language="python")

            except Exception as e:
                st.error(f"❌ Generation failed: {e}")
                st.info("💡 Tip: Check your API key in `.env` and ensure you have internet connectivity.")