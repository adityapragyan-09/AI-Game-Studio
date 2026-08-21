"""
AI Game Studio - Streamlit Application.

A multi-agent AI system for generating playable pygame games.
"""

import streamlit as st
import os
import logging
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="AI Game Studio",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import utilities
from utils.code_extraction import extract_code, full_validation, ExtractionResult
from utils.audio_safety import ensure_audio_safety_ast
from utils.error_handling import get_user_error, format_error_for_ui, log_generation_error
from utils.retry import gemini_circuit_breaker, CircuitBreakerOpenError

# Try to import crew
try:
    from crew import get_crew, crew
    CREW_AVAILABLE = True
except (ValueError, ImportError) as e:
    CREW_AVAILABLE = False
    crew = None
    logger.warning(f"Crew not available: {e}")

# Demo games (pre-generated for fallback)
DEMO_GAMES = {
    "Wigglebottom's Wobbly Warp": "demo_wigglebottom.py",
    "Neon Runner": "demo_neon_runner.py",
    "Orbit Defense": "demo_orbit_defense.py",
}

# Session state initialization
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False
if 'last_generation_time' not in st.session_state:
    st.session_state.last_generation_time = 0
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = None
if 'generation_error' not in st.session_state:
    st.session_state.generation_error = None


def check_rate_limit() -> bool:
    """Check if enough time has passed since last generation."""
    MIN_INTERVAL = 30  # seconds
    elapsed = time.time() - st.session_state.last_generation_time
    if elapsed < MIN_INTERVAL:
        remaining = int(MIN_INTERVAL - elapsed)
        st.warning(f"⏳ Please wait {remaining}s before generating another game.")
        return False
    return True


def validate_environment() -> Optional[str]:
    """Validate that required environment is configured."""
    if not os.getenv("GEMINI_API_KEY"):
        return "Gemini API configuration is missing. Please configure GEMINI_API_KEY in your environment."
    return None


def run_generation_pipeline(game_idea: str) -> tuple[Optional[str], Optional[str]]:
    """
    Run the full generation pipeline.

    Returns:
        (generated_code, error_message)
    """
    if not CREW_AVAILABLE:
        return None, "AI generation is not available. Please check server configuration."

    # Check circuit breaker
    if gemini_circuit_breaker.state == "OPEN":
        return None, "AI service is temporarily unavailable due to repeated failures. Please try again later."

    try:
        # Get crew
        game_crew = get_crew()

        # Run crew with timeout protection
        logger.info(f"Starting generation for: {game_idea[:50]}...")
        start_time = time.time()

        result = game_crew.kickoff(inputs={"game_idea": game_idea})

        duration = time.time() - start_time
        logger.info(f"Generation completed in {duration:.1f}s")

        # Extract raw output
        raw_output = str(result)

        # Extract code using robust extraction
        extraction_result = extract_code(raw_output)

        if not extraction_result.success:
            logger.warning(f"Code extraction failed: {extraction_result.warnings}")
            return None, "Failed to extract valid code from AI response. Please try again."

        generated_code = extraction_result.code

        # Apply audio safety
        generated_code = ensure_audio_safety_ast(generated_code)

        # Full validation
        valid, issues = full_validation(generated_code)

        if not valid:
            logger.warning(f"Validation failed: {issues}")
            # Don't fail - save anyway but warn
            issues_str = "; ".join(issues[:5])  # Limit to first 5 issues
            return generated_code, f"Validation warnings (game saved anyway): {issues_str}"

        return generated_code, None

    except CircuitBreakerOpenError as e:
        log_generation_error("circuit_breaker", e)
        return None, "AI service is temporarily unavailable. Please try again in a moment."
    except Exception as e:
        log_generation_error("pipeline", e, {"game_idea": game_idea[:100]})
        user_error = get_user_error(e)
        return None, format_error_for_ui(e)


def save_generated_code(code: str) -> str:
    """Save generated code to outputs directory."""
    os.makedirs("outputs", exist_ok=True)
    output_path = os.path.join("outputs", "generated_game.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    return os.path.abspath(output_path)


# ============================================================
# STREAMLIT UI
# ============================================================

# Header
st.title("🎮 AI Game Development Studio")
st.caption("Multi-agent AI system for generating playable pygame games")

# Environment check
env_error = validate_environment()
if env_error:
    st.error(f"⚠️ **Configuration Required**: {env_error}")
    st.info("Create a `.env` file with your `GEMINI_API_KEY` or set it as an environment variable.")
    st.code("GEMINI_API_KEY=your_key_here", language="bash")
    st.stop()

# Game idea input
game_idea = st.text_area(
    "Enter your game idea",
    placeholder="Example: Endless cyberpunk runner with boss fights and neon visuals",
    height=100,
    help="Describe the game you want to create. Be specific about mechanics, theme, and style."
)

# Example prompts
with st.expander("💡 Example Prompts", expanded=False):
    examples = [
        "Endless runner with procedurally generated obstacles and power-ups",
        "Top-down shooter with waves of enemies and upgrade system",
        "Platformer with physics-based movement and collectibles",
        "Puzzle game with falling blocks and line clearing",
        "Space shooter with asteroid field and boss battles",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
            st.session_state.game_idea_input = ex
            st.rerun()

# Use session state for example prompts
if 'game_idea_input' in st.session_state:
    game_idea = st.session_state.game_idea_input
    del st.session_state.game_idea_input

# Demo mode section
st.divider()
st.subheader("🎮 Demo Mode (No API Key Required)")
st.caption("Explore pre-generated games to see what the system can create")

demo_cols = st.columns(len(DEMO_GAMES))
for i, (title, filename) in enumerate(DEMO_GAMES.items()):
    with demo_cols[i]:
        if st.button(f"📥 {title}", use_container_width=True, key=f"demo_{i}"):
            # Load demo game
            demo_path = os.path.join("demos", filename)
            if os.path.exists(demo_path):
                with open(demo_path, "r", encoding="utf-8") as f:
                    st.session_state.generated_code = f.read()
                st.session_state.generation_error = None
                st.success(f"Loaded demo: {title}")
                st.rerun()
            else:
                st.error(f"Demo file not found: {demo_path}")

# Main generation button
st.divider()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_disabled = st.session_state.generation_in_progress or not game_idea.strip()
    if st.button(
        "🚀 Generate Game",
        type="primary",
        disabled=generate_disabled,
        use_container_width=True
    ):
        if not check_rate_limit():
            st.stop()

        st.session_state.generation_in_progress = True
        st.session_state.generation_error = None
        st.session_state.generated_code = None
        st.rerun()

# Generation progress
if st.session_state.generation_in_progress:
    with st.status("🤖 AI Agents are building your game...", expanded=True) as status:
        # Show progress steps
        steps = [
            ("🎨 Designing game concept", "design"),
            ("💻 Generating game code", "develop"),
            ("⚡ Optimizing performance", "optimize"),
            ("🔍 Running QA checks", "qa"),
            ("✅ Validating output", "validate"),
        ]

        for step_name, step_key in steps:
            st.write(f"{step_name}...")
            time.sleep(0.5)  # Visual feedback

        # Run actual generation
        generated_code, error = run_generation_pipeline(game_idea)

        if error:
            st.session_state.generation_error = error
            status.update(label="❌ Generation failed", state="error")
        else:
            st.session_state.generated_code = generated_code
            st.session_state.last_generation_time = time.time()
            status.update(label="✅ Game generated successfully!", state="complete")

        st.session_state.generation_in_progress = False
        time.sleep(1)
        st.rerun()

# Display error
if st.session_state.generation_error:
    st.error(st.session_state.generation_error)
    if st.button("🔄 Try Again"):
        st.session_state.generation_error = None
        st.rerun()

# Display generated code
if st.session_state.generated_code:
    st.success("✅ Game generated successfully!")

    # Save to file
    abs_path = save_generated_code(st.session_state.generated_code)
    st.info(f"📁 Saved to: `{abs_path}`")

    # Download button
    st.download_button(
        label="⬇️ Download Game",
        data=st.session_state.generated_code,
        file_name="generated_game.py",
        mime="text/x-python",
        use_container_width=True
    )

    # Run instructions
    st.code("python outputs/generated_game.py", language="bash")

    # Preview
    with st.expander("👀 Preview Generated Code", expanded=False):
        st.code(st.session_state.generated_code, language="python", line_numbers=True)

    # Clear button
    if st.button("🗑️ Clear & Generate New"):
        st.session_state.generated_code = None
        st.session_state.generation_error = None
        st.rerun()

# Footer
st.divider()
st.caption(
    "AI Game Studio • Built with CrewAI + Gemini + Streamlit + Pygame • "
    "Generated code is untrusted - review before execution"
)