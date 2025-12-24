# 📘 LazyTrainer - Developer Handbook

This document serves as the primary reference for developing, running, and maintaining the LazyTrainer backend and infrastructure.

---

## 🛠️ 1. Environment Setup
**Context:** All commands regarding the backend must be run from the `backend/` directory with the virtual environment active.

### Activate Virtual Environment
* **Windows (PowerShell):**
    ```powershell
    backend\venv\Scripts\activate
    ```
* **Mac/Linux:**
    ```bash
    source backend/venv/bin/activate
    ```

### 🔐 1.1 Configuration (.env)
We use a `.env` file to manage secrets. **Never commit this file to GitHub.**
Create a file named `.env` inside `backend/` with the following content:

```ini
# Database Connection
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/postgres

# AI Provider (OpenAI)
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_MODEL_NAME=gpt-4o

```

---

## 🗄️ 2. Database Management (Alembic)

We use **Alembic** for database migrations. Never modify the PostgreSQL schema manually. Use this workflow when you change `models.py`.

### A. The Migration Workflow

1. **Modify** your `models.py` file.
2. **Generate** a migration script (snapshot):
```bash
cd backend
alembic revision --autogenerate -m "Describe your change here"

```


3. **🔍 CRITICAL: Review the File**
* Go to `backend/alembic/versions/` and open the new file.
* **Check imports:** If the change involves vectors, ensure `import pgvector` is present.
* **Check logic:** Ensure the SQL commands look correct.


4. **Apply** the changes to the Database:
```bash
alembic upgrade head

```



### B. Undo/Reset Changes

* **Undo last migration:** `alembic downgrade -1`
* **Hard Reset (If corrupted):**
1. Open PgAdmin Query Tool.
2. Run: `DROP TABLE IF EXISTS alembic_version;` (plus other tables like `exercises`).
3. Re-run: `alembic upgrade head`



---

## 🌱 3. Data Seeding (Populating the DB)

To fill the database with initial exercises.

### A. Run with Real AI Embeddings (Recommended)

You need to set the API Key temporarily in your terminal session before running the script (or ensure it's in your `.env` file).

**Windows (PowerShell):**

```powershell
$env:OPENAI_API_KEY="sk-YOUR-KEY-HERE"
python -m src.scripts.seed_db

```

**Mac/Linux:**

```bash
export OPENAI_API_KEY="sk-YOUR-KEY-HERE"
python -m src.scripts.seed_db

```

---

## 🚀 4. Running the Server

To start the FastAPI server with **hot-reload**:

```bash
cd backend
uvicorn src.main:app --reload

```

* **API URL:** `http://127.0.0.1:8000`
* **Swagger UI (Docs):** `http://127.0.0.1:8000/docs`

---

## 🐳 5. Infrastructure (Docker)

* **Start Database:** `docker-compose up -d`
* **Stop Database:** `docker-compose down`
* **View Logs:** `docker logs lazytrainer_db`

### 🖥️ PgAdmin (Visual Interface)

* **URL:** `http://localhost:5050`
* **Login:** `admin@admin.com` / `admin`
* **Connect:** Host: `db` | User: `postgres` | Pass: `password`

---

## 📦 6. Dependency Management

* **Install package:** `pip install package_name`
* **Save dependencies:** `pip freeze > requirements.txt`
* **Install from requirements:** `pip install -r requirements.txt`

---

## 📂 7. Project Structure Reference

```text
backend/
├── alembic/                # Migration scripts
├── src/
│   ├── api/                
│   │   ├── routes.py       # Endpoints (User Profile -> AI Trigger)
│   │   └── schemas.py      # Pydantic Models (Request/Response)
│   ├── crew/               # 🧠 THE BRAIN (AI Logic)
│   │   ├── agents.py       # Definition of Agents (Roles, Backstory)
│   │   ├── tasks.py        # Definition of Tasks (Instructions)
│   │   ├── tools.py        # Custom Tools (SQL/Vector Search Logic)
│   │   └── main.py         # Orchestrator (Crew runner)
│   ├── database/           
│   │   ├── connection.py   # DB Session
│   │   └── models.py       # SQL Tables
│   ├── scripts/            # Utility scripts
│   │   └── seed_db.py      # Database populator
│   └── main.py             # App Entry Point
├── .env                    # Secrets (API Keys) - NOT IN GIT
├── alembic.ini             # Alembic Config
└── requirements.txt        # Dependencies

```

---

## 🧠 8. AI & Agents Troubleshooting

### Common Issues

* **"Action Input is not a valid key..."**:
* *Cause:* The Agent sent a complex Python object (List/Dict) to a Tool that expects a String.
* *Fix:* Simplify the Tool's input schema in `tools.py` (e.g., ask for comma-separated strings).


* **"Context Window Exceeded"**:
* *Cause:* The Agent retrieved too many exercises or the history is too long.
* *Fix:* Reduce the `limit` in `ExerciseRetrieverTool` or clean up the `backstory`.


* **Agent Hallucinations (Inventing Exercises)**:
* *Fix:* Reinforce the prompt in `agents.py` with: "You must ONLY use the provided tool. Do not guess."



```
