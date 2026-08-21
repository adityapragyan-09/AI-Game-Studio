# 🎮 AI Game Studio

**A multi-agent AI system that generates complete, playable pygame games from natural language descriptions.**

![AI Game Studio](https://img.shields.io/badge/AI-Game%20Studio-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red?style=for-the-badge)
![CrewAI](https://img.shields.io/badge/CrewAI-0.144-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-purple?style=for-the-badge)
![Pygame](https://img.shields.io/badge/Pygame-2.5-yellow?style=for-the-badge)

---

## 🎯 Overview

AI Game Studio demonstrates the power of **multi-agent AI collaboration** for creative coding tasks. Four specialized AI agents work together in a sequential pipeline to design, develop, optimize, and quality-assure complete pygame games — all from a single text prompt.

### Key Features

- 🤖 **4-Agent Pipeline**: Designer → Developer → Optimizer → QA
- 🎨 **Asset-Free Generation**: Pure pygame primitives (no external images/sounds/fonts)
- 🔒 **Security-First**: AST-based validation, import allowlisting, dangerous pattern detection
- ⚡ **Resilient AI**: Timeout, retry, rate-limit handling, circuit breaker
- 🧪 **Fully Tested**: 75+ unit/integration tests covering extraction, validation, security
- 🎮 **Demo Mode**: Pre-generated games work without API keys
- 📦 **Production Ready**: Structured output, comprehensive logging, error handling

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER (Browser)                                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI (app.py)                               │
│  • Text area for game idea                                                  │
│  • "Generate Game" button with progress tracking                            │
│  • Demo mode for instant exploration                                        │
│  • Code preview & download                                                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CREWAI CREW (crew.py) — SEQUENTIAL                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  DESIGNER    │→ │  DEVELOPER   │→ │  OPTIMIZER   │→ │     QA       │    │
│  │  (design)    │  │  (develop)   │  │  (optimize)  │  │   (qa)       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│       │                │                │                │                   │
│       ▼                ▼                ▼                ▼                   │
│  Game Design      Raw Python       Optimized       Final Fixed              │
│  Document         Game Code        Game Code      Game Code                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    POST-PROCESSING (utils/)                                 │
│  1. extract_code()       — Structured output → fenced blocks → heuristic    │
│  2. ensure_audio_safety() — AST-based try/except wrapping                   │
│  3. full_validation()     — Syntax + Structure + Imports + Security scan   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FILE OUTPUT (outputs/generated_game.py)              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      USER EXECUTES: python outputs/generated_game.py        │
│                           (Pygame window opens)                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent Pipeline

### 1. 🎨 Game Designer
- **Role**: Senior Game Designer
- **Input**: User's game idea
- **Output**: Structured game design document (mechanics, controls, enemies, progression, visual style)
- **Constraints**: Asset-free, pygame primitives only, no audio

### 2. 💻 Game Developer
- **Role**: Expert Python Game Developer
- **Input**: Game design document
- **Output**: Complete executable pygame game code
- **Constraints**: Raw Python only, no markdown, audio safety pattern, asset-free

### 3. ⚡ Performance Optimizer
- **Role**: Performance Optimization Engineer
- **Input**: Developer's game code
- **Output**: Optimized game code (FPS stability, memory, visual polish)
- **Constraints**: Preserve all gameplay, maintain audio safety, no new assets

### 4. 🔍 QA Engineer
- **Role**: Game QA Engineer
- **Input**: Optimized game code
- **Output**: Final validated game code
- **Responsibilities**: Bug fixing, audio safety audit, asset safety audit, gameplay quality

---

## 🛡️ Security & Safety

### Generated Code Protection

| Layer | Implementation |
|-------|----------------|
| **AST Security Scan** | Detects `eval`, `exec`, `os.system`, `subprocess`, network calls, dangerous imports |
| **Import Allowlist** | Only `pygame`, `random`, `sys`, `os`, `math`, `time`, `json`, `typing`, `dataclasses`, `collections`, `itertools`, `functools` |
| **Structure Validation** | Verifies pygame.init(), display, game loop, clock.tick(), pygame.quit(), main guard |
| **Syntax Validation** | Full AST parse before execution |
| **Audio Safety** | AST-based transformation wraps `pygame.mixer.init()` in try/except |

### Execution Safety

> ⚠️ **Important**: AI-generated code is **untrusted**. The application:
> - **Never auto-executes** generated code on the server
> - Provides download button for local execution
> - Runs security validation before saving
> - Clearly warns users to review code before running

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Gemini API key (get one at [Google AI Studio](https://aistudio.google.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/adityapragyan-09/AI-Game-Studio.git
cd AI-Game-Studio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Running

```bash
# Start the Streamlit app
streamlit run app.py

# Open http://localhost:8501 in your browser
```

### Usage

1. **Enter a game idea** (or click an example prompt)
2. **Click "Generate Game"** — watch the 4-agent pipeline in action
3. **Download the generated game** (`generated_game.py`)
4. **Run locally**: `python outputs/generated_game.py`

### Demo Mode (No API Key Required)

Click any **"Demo Game"** button to instantly load and explore pre-generated games:
- **Wigglebottom's Wobbly Warp** — Endless runner with unique characters
- **Neon Runner** — Cyberpunk endless runner with glow effects
- **Orbit Defense** — Circular tower defense game

---

## 💡 Example Prompts

| Prompt | Style |
|--------|-------|
| "Endless cyberpunk runner with neon visuals, boss fights, and power-ups" | Cyberpunk runner |
| "Top-down space shooter with asteroid waves, ship upgrades, and bullet hell patterns" | Space shooter |
| "Physics-based platformer with momentum, wall jumps, and collectible stars" | Platformer |
| "Puzzle game with falling colored blocks, chain reactions, and combo scoring" | Puzzle |
| "Arena survival with waves of enemies, experience system, and ability choices" | Survival |

---

## 📁 Project Structure

```
AI_Game_Studio/
├── app.py                      # Streamlit UI entry point
├── crew.py                     # CrewAI crew configuration
├── llm.py                      # Centralized LLM configuration
├── requirements.txt            # Pinned dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
│
├── agents/                     # CrewAI agent definitions
│   ├── designer.py            # Game Designer agent
│   ├── developer.py           # Game Developer agent
│   ├── optimizer.py           # Optimizer agent
│   └── qa.py                  # QA Engineer agent
│
├── tasks/                      # CrewAI task definitions
│   ├── design_task.py         # Design task with structured output
│   ├── develop_task.py        # Development task with structured output
│   ├── optimize_task.py       # Optimization task with structured output
│   └── qa_task.py             # QA task with structured output
│
├── models/                     # Pydantic models for structured output
│   └── game_output.py         # GameDesign, GameCode, task output schemas
│
├── utils/                      # Utility modules
│   ├── code_extraction.py     # Robust code extraction & validation
│   ├── audio_safety.py        # AST-based audio safety transformation
│   ├── error_handling.py      # User-friendly error mapping
│   └── retry.py               # Retry logic & circuit breaker
│
├── tests/                      # Test suite (75+ tests)
│   ├── test_code_extraction.py
│   ├── test_error_handling.py
│   ├── test_audio_safety.py
│   ├── test_retry.py
│   └── test_validation.py
│
├── demos/                      # Pre-generated demo games
│   ├── demo_wigglebottom.py
│   ├── demo_neon_runner.py
│   └── demo_orbit_defense.py
│
└── outputs/                    # Generated games (gitignored)
    └── generated_game.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_code_extraction.py -v
pytest tests/test_validation.py -v
pytest tests/test_error_handling.py -v
pytest tests/test_audio_safety.py -v
pytest tests/test_retry.py -v

# With coverage (utility modules only)
pytest tests/ --cov=utils --cov=agents --cov=tasks
```

### Test Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| Code Extraction | 22 | ~95% |
| Error Handling | 12 | ~90% |
| Audio Safety | 7 | ~85% |
| Retry/Circuit Breaker | 10 | ~90% |
| Validation Integration | 5 | ~95% |
| **Total (utility modules)** | **75** | **~95%** |

> **Note**: The above coverage percentages apply to the measured utility modules (code extraction, validation, error handling, retry, audio safety). Full application coverage including the Streamlit UI (`app.py`), CrewAI orchestration (`crew.py`), and end-to-end pipeline is not currently measured.

### Key Test Categories

- ✅ **Code Extraction**: Structured output, fenced blocks, heuristic, priority ordering
- ✅ **Syntax Validation**: Valid/invalid Python, empty code
- ✅ **Game Structure**: Required imports, pygame.init(), display, loop, clock, quit, main guard
- ✅ **Import Validation**: Allowlist enforcement, dangerous import detection
- ✅ **Security Scanning**: eval, exec, os.system, subprocess, network calls
- ✅ **Error Mapping**: 429, 401, 5xx, timeout, network → user-friendly messages
- ✅ **Retry Logic**: Exponential backoff, jitter, circuit breaker states
- ✅ **Audio Safety**: Wrapping, double-wrap prevention, syntax error handling

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `SERPER_API_KEY` | No | Serper API key (for future web search features) |

### LLM Configuration (`llm.py`)

```python
LLMConfig(
    model="gemini/gemini-3.5-flash",  # Model name
    timeout=120,                       # Request timeout (seconds)
    max_retries=3,                     # Max retry attempts
    temperature=0.3,                   # Creativity (0.0-1.0)
    top_p=0.95,                        # Nucleus sampling
    top_k=40,                          # Top-k sampling
)
```

### Rate Limiting

- **Minimum interval**: 30 seconds between generations
- **Circuit breaker**: Opens after 5 consecutive failures, recovers after 60s
- **Max retries**: 3 attempts with exponential backoff (1s, 2s, 4s + jitter)

---

## 🔧 Development

### Adding a New Agent

1. Create agent in `agents/new_agent.py`
2. Create task in `tasks/new_task.py` with structured output
3. Add to `crew.py` agent/task lists
4. Add validation in `utils/code_extraction.py` if needed

### Extending Validation

Add new checks to `full_validation()` in `utils/code_extraction.py`:

```python
def my_custom_check(code: str) -> Tuple[bool, List[str]]:
    # Your validation logic
    return valid, issues

# In full_validation():
valid, issues = my_custom_check(code)
if not valid:
    all_issues.extend([f"CUSTOM: {i}" for i in issues])
```

---

## 📦 Deployment

### Streamlit Cloud (Recommended)

1. Push to GitHub
2. Connect repo to [Streamlit Community Cloud](https://streamlit.io/cloud)
3. Add `GEMINI_API_KEY` in Secrets
4. Deploy!

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Pygame Execution Note

> **Important**: Pygame requires a display. For cloud deployment:
> - Streamlit UI runs in browser (no display needed)
> - Generated games must be downloaded and run locally
> - For browser-based games, consider [Pygbag](https://github.com/pygame-web/pygbag) (WASM compilation)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Gemini API configuration is missing" | Create `.env` with `GEMINI_API_KEY=your_key` |
| "AI service is temporarily busy" | Wait 30s, try again (rate limit) |
| "Generation failed: timeout" | Increase `timeout` in `llm.py` |
| Pygame window doesn't open | Ensure display available; run locally not via SSH |
| Import errors | Run `pip install -r requirements.txt` in venv |
| Tests fail | Ensure `pytest` installed in venv |

---

## 📝 Known Limitations

1. **No auto-execution** — Generated games must be downloaded and run locally
2. **Single-file games** — All code in one `.py` file (by design)
3. **No external assets** — Pure pygame primitives only (by design)
4. **Gemini dependency** — Requires API key; demo mode available without
5. **Sequential pipeline** — ~30-60s generation time (4 sequential agent API calls)
6. **Gemini quota** — Live generation consumes multiple API requests per generation. The application includes rate limiting and Demo Mode to remain usable when live generation is unavailable.
7. **Python 3.11+** — Required for `ast.unparse` and modern typing

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes with tests
4. Run test suite: `pytest tests/ -v`
5. Submit PR with description

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **CrewAI** — Multi-agent orchestration framework
- **Google Gemini** — LLM provider
- **Streamlit** — Rapid UI development
- **Pygame** — Game engine
- **Pydantic** — Structured validation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/adityapragyan-09/AI-Game-Studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adityapragyan-09/AI-Game-Studio/discussions)

---

<div align="center">

**Built with ❤️ using CrewAI + Gemini + Streamlit + Pygame**

*Demonstrating multi-agent AI for creative code generation*

</div>