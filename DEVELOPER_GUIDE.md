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

### Troubleshooting
If you see a "Script execution disabled" error on Windows:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

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
* **Check imports:** If the change involves vectors, ensure `import pgvector` is present at the top.
* **Check logic:** Ensure the SQL commands look correct.


4. **Apply** the changes to the Database:
```bash
alembic upgrade head

```



### B. Undo Changes

If a migration breaks the app, you can roll back the database to the previous state:

```bash
alembic downgrade -1

```

### C. Check Status

To see which migration revision the database is currently on:

```bash
alembic current

```

### D. Hard Reset (Fix Corrupted State)

If you delete tables manually or mess up the migration history, you must reset Alembic's memory:

1. Open PgAdmin Query Tool.
2. Run: `DROP TABLE IF EXISTS alembic_version;` (and drop any other tables you want to reset).
3. Re-run migrations: `alembic upgrade head`

---

## 🌱 3. Data Seeding (Populating the DB)

To fill the database with initial exercises.

### A. Run with Real AI Embeddings (Recommended)

You need to set the API Key temporarily in your terminal session before running the script.

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

### B. Run with Dummy Data (No API Key)

The script will auto-detect the missing key and insert zero-vectors (app works, but semantic search won't).

```bash
python -m src.scripts.seed_db

```

---

## 🚀 4. Running the Server

To start the FastAPI server with **hot-reload** (updates automatically when you save code):

```bash
cd backend
uvicorn src.main:app --reload

```

* **API URL:** `http://127.0.0.1:8000`
* **Swagger UI (Docs):** `http://127.0.0.1:8000/docs`

---

## 🐳 5. Infrastructure (Docker)

To manage the PostgreSQL database container.

* **Start Database:** `docker-compose up -d`
* **Stop Database:** `docker-compose down`
* **View Logs:** `docker logs lazytrainer_db`

### 🖥️ PgAdmin (Visual Interface)

* **URL:** `http://localhost:5050`
* **Login:** `admin@admin.com` / `admin`
* **Connect to Server:**
* Host: `db`
* Username: `postgres`
* Password: `password`



### Database Troubleshooting

If you get a `type "vector" does not exist` error, run this to force enable the extension:

```powershell
docker exec -it lazytrainer_db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

```

---

## 📦 6. Dependency Management

We use `pip` to manage Python packages.

* **Install a new package:** `pip install package_name`
* **Save dependencies:** `pip freeze > requirements.txt`
* **Install from requirements:** `pip install -r requirements.txt`

---

## 📂 7. Project Structure Reference

```text
backend/
├── alembic/                # Migration scripts
├── src/
│   ├── api/                
│   │   ├── routes.py       # API Endpoints (GET, POST)
│   │   └── schemas.py      # Data Models (Pydantic)
│   ├── crew/               # AI Agents & Logic
│   ├── database/           
│   │   ├── connection.py   # DB Session Management
│   │   └── models.py       # SQL Tables Definitions
│   ├── scripts/            # Utility scripts (Seeding, etc.)
│   │   └── seed_db.py      # Database populator
│   └── main.py             # App Entry Point (Router wiring)
├── alembic.ini             # Alembic Config
└── requirements.txt        # Dependencies

```
