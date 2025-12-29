# 🏋️‍♂️ LazyTrainer - AI-Powered Personal Training Agent

> **Status:** 🚀 Backend Complete | 🚧 Phase 3: Frontend (Flutter) Development

**LazyTrainer** is a State-of-the-Art (SoTA) application designed to generate hyper-personalized training programs. Unlike standard fitness apps that rely on static templates, LazyTrainer uses a **Multi-Agent AI** architecture to analyze user biomechanics, injuries, and training history, retrieving verified exercises from a vector database to build safe, effective, and evolving routines.

---

## 🏗️ Architecture

The system utilizes an **Asynchronous Event-Driven Architecture** combined with **Neuro-Symbolic AI** (LLM Logic + SQL Strictness).

```mermaid
graph LR
    A[Flutter App] <-->|HTTP/REST| B(FastAPI Backend)
    B <-->|Read/Write| D[(PostgreSQL + pgvector)]
    
    subgraph "The AI Brain (CrewAI)"
        S[Strategist Agent] -->|Split & Volume| L[Selector Agent]
        L -->|Exercise Search| D
        L -->|Exercise List| C[Coach Agent]
        C -->|Sets/Reps/JSON| B
    end

```

## 🛠️ Tech Stack

### Backend & Infrastructure

* **Language:** Python 3.12
* **Framework:** FastAPI (Async)
* **Database:** PostgreSQL (with `pgvector` extension)
* **ORM:** SQLAlchemy + Alembic (Migrations)
* **AI Orchestrator:** CrewAI (Multi-Agent Systems)
* **Containerization:** Docker & Docker Compose

### Frontend (Upcoming)

* **Framework:** Flutter (Dart)
* **State Management:** Riverpod
* **Communication:** REST API

---

## ⚡ Features

### Core Infrastructure

* [x] **Dockerized Environment:** One-command setup for Database and Services.
* [x] **Vector Database:** Schema designed for semantic search of exercises (RAG).
* [x] **Smart Data Seeding:** Automated script to populate DB with biomechanics metadata & embeddings.
* [x] **Database Migrations:** Version control for the DB schema using Alembic.

### AI & Agents (The "Brain")

* [x] **Multi-Agent Crew:** Specialized agents for Strategy (Split), Selection (Exercises), and Coaching (Math).
* [x] **Hallucination Guardrails:** Strict SQL-based tools ensure the AI cannot invent non-existent exercises.
* [x] **Contextual Equipment Merging:** Deterministic logic handles "Gym" vs "Park" vs "Home" equipment availability.

### Lifecycle Management (The "Trainer")

* [x] **Persistence:** Workout plans are saved as structured JSONB for historical tracking.
* [x] **Exercise Swapping:** "Swap" endpoint uses AI to find biomechanical equivalents (e.g., Lat Pulldown -> Pull-up) without breaking the plan.
* [x] **Difficulty Adjustment:** "Adjust" endpoint scales volume or changes methods (e.g., Standard -> EMOM) on the fly.
* [x] **Progression System:** Generates *next* month's program based on the history and feedback of the *previous* block.

---

## 🚀 Getting Started

### Prerequisites

* Docker Desktop (Running)
* Python 3.12+
* OpenAI API Key (For generating embeddings & Agent Logic)

### 1. Clone & Setup

```bash
git clone [https://github.com/EmanueleCeglia/LazyTrainerApp.git](https://github.com/EmanueleCeglia/LazyTrainerApp.git)
cd LazyTrainerApp

```

### 2. Infrastructure (Start Database)

Start the PostgreSQL container with pgvector support:

```bash
docker-compose up -d

```

### 3. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

```

### 4. Configuration (.env)

Create a `.env` file in the `backend/` directory to store your secrets.
**Do not commit this file.**

```ini
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/postgres

# AI Keys
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_MODEL_NAME=gpt-4o

```

### 5. Database Initialization

Apply the migrations to create tables in the running container:

```bash
alembic upgrade head

```

### 6. Seed the Database (Populate Data)

This script fills the empty database with exercises and generates their AI embeddings.
*(Note: Ensure your .env file is set up or export the key manually)*.

```bash
python -m src.scripts.seed_db

```

### 7. Run the Server

```bash
uvicorn src.main:app --reload

```

* **API URL:** `http://127.0.0.1:8000`
* **Swagger Documentation:** `http://127.0.0.1:8000/docs`

---

## 📂 Project Structure

```text
LazyTrainerApp/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI Routes (Create, Swap, Adjust)
│   │   ├── crew/         # 🧠 THE BRAIN: Multi-Agent Logic
│   │   │   ├── agents.py     # Strategist, Selector, Coach definitions
│   │   │   ├── tasks.py      # Sequential Task Pipeline
│   │   │   ├── tools.py      # Vector Search Tool
│   │   │   ├── main.py       # Orchestrator
│   │   │   └── modifier.py   # Lightweight runner for Swaps/Adjustments
│   │   ├── database/     # DB Connection & SQLAlchemy Models
│   │   ├── scripts/      # Data Seeding & Utility Scripts
│   │   └── main.py       # Application Entry Point
│   ├── alembic/          # Database Migration scripts
│   └── requirements.txt  # Python Dependencies
├── frontend/             # Flutter Application (Under Construction)
├── docker-compose.yml    # Infrastructure orchestration
└── README.md

```

---

## 📄 License

This project is licensed under the MIT License.

```