# 🏋️‍♂️ LazyTrainer - AI-Powered Personal Training Agent

> **Status:** 🚧 In Development (Backend AI Integration Phase)

**LazyTrainer** is a State-of-the-Art (SoTA) application designed to generate hyper-personalized training programs. Unlike standard fitness apps that rely on static templates, LazyTrainer uses an **Agentic AI** architecture to analyze user biomechanics, injuries, and goals, retrieving verified exercises from a vector database to build safe, effective routines.

---

## 🏗️ Architecture

The system utilizes an **Asynchronous Event-Driven Architecture** combined with **Hybrid RAG** (Semantic + SQL filtering) to ensure high-quality outputs.

```mermaid
graph LR
    A[Flutter App] -->|Request| B(FastAPI Backend)
    B -->|Async Task| C{CrewAI Orchestrator}
    C -->|Hybrid Search| D[(PostgreSQL + pgvector)]
    D -->|Context| C
    C -->|JSON Program| B
    B -->|WebSocket| A

```

## 🛠️ Tech Stack

### Backend & Infrastructure

* **Language:** Python 3.12
* **Framework:** FastAPI (Async)
* **Database:** PostgreSQL (with `pgvector` extension)
* **ORM:** SQLAlchemy + Alembic (Migrations)
* **AI Orchestrator:** CrewAI (Multi-Agent Systems)
* **Containerization:** Docker & Docker Compose

### Frontend (Planned)

* **Framework:** Flutter (Dart)
* **State Management:** Riverpod
* **Communication:** WebSockets (Real-time agent feedback)

---

## ⚡ Features

* [x] **Dockerized Environment:** One-command setup for Database and Services.
* [x] **Vector Database:** Schema designed for semantic search of exercises (RAG).
* [x] **Smart Data Seeding:** Automated script to populate DB with biomechanics metadata & embeddings.
* [x] **Clean Architecture:** Modular code structure (`api`, `crew`, `database`, `scripts`).
* [x] **Database Migrations:** Version control for the DB schema using Alembic.
* [x] **Agentic Workflow:** "Biomechanics" agent capable of querying the DB for safe exercises.
* [ ] **Mobile Interface:** iOS/Android app.

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
│   │   ├── api/          # FastAPI Routes (Endpoints) & Schemas (Pydantic)
│   │   ├── crew/         # 🧠 THE BRAIN: Agents, Tasks, Tools
│   │   ├── database/     # DB Connection & SQLAlchemy Models
│   │   ├── scripts/      # Data Seeding & Utility Scripts
│   │   └── main.py       # Application Entry Point
│   ├── alembic/          # Database Migration scripts
│   └── requirements.txt  # Python Dependencies
├── frontend/             # Flutter Application (Coming Soon)
├── docker-compose.yml    # Infrastructure orchestration
└── README.md

```

---

## 📄 License

This project is licensed under the MIT License.

```