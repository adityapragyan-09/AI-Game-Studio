# 🎮 AI Game Studio

An AI-powered multi-agent game generation system built using CrewAI, Streamlit, and Pygame.

This project autonomously generates playable 2D pygame games using multiple AI agents for:
- game design
- development
- optimization
- QA testing

---

# 🚀 Features

- 🤖 Multi-Agent AI Architecture using CrewAI
- 🎮 Automatic Playable Game Generation
- 🧠 AI Game Designer Agent
- 💻 AI Developer Agent
- 🛠️ AI Optimizer Agent
- ✅ AI QA Testing Agent
- 🌐 Streamlit Frontend Interface
- ⚡ Gemini API Integration
- 📂 Automatic Game File Generation
- 🧩 Modular Project Structure

---

# 🖼️ Generated Game Example

The system generated this playable pygame game:

- Dynamic scoring system
- Zone progression
- Enemy avoidance gameplay
- Increasing difficulty
- Restart functionality

## Example Gameplay Screenshot

![Generated Game](Screenshot%202026-05-20%20145441.png)

---

# 🏗️ Project Architecture

```txt
User Prompt
     ↓
Designer Agent
     ↓
Developer Agent
     ↓
QA Agent
     ↓
Optimizer Agent
     ↓
Playable Pygame Game
```

---

# 📁 Project Structure

```txt
AI_Game_Studio/
│
├── agents/
│   ├── designer.py
│   ├── developer.py
│   ├── optimizer.py
│   └── qa.py
│
├── tasks/
│   ├── design_task.py
│   ├── develop_task.py
│   ├── optimize_task.py
│   └── qa_task.py
│
├── outputs/
│   └── generated_game.py
│
├── app.py
├── crew.py
├── llm.py
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Tech Stack

- Python
- CrewAI
- Streamlit
- Pygame
- Gemini API

---

# ▶️ Run Locally

## 1️⃣ Clone Repository

```bash
git clone YOUR_GITHUB_REPO_LINK
cd AI_Game_Studio
```

---

## 2️⃣ Create Virtual Environment

```bash
py -3.11 -m venv venv
```

Activate:

```bash
.\venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Add API Key

Create `.env`

```env
GEMINI_API_KEY=YOUR_API_KEY
```

---

## 5️⃣ Run Streamlit App

```bash
streamlit run app.py
```

---

# 🎯 Example Prompt

```txt
Create a simple pygame survival game where the player avoids enemies, scores points over time, and the game gets harder gradually.
```

---

# 📌 Future Improvements

- AI-generated sprites
- Procedural level generation
- Better enemy AI
- Multiplayer generation
- Save system
- Reinforcement-learning NPCs

---

# 📜 License

This project is open-source and available under the MIT License.

---

# 👨‍💻 Developer

Built by Aditya Pragyan using AI orchestration and autonomous agent systems.
