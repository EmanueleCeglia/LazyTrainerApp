
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

---

## 🚀 3. Running the Server

To start the FastAPI server with **hot-reload** (updates automatically when you save code):

```bash
cd backend
uvicorn src.main:app --reload

```

* **API URL:** `http://127.0.0.1:8000`
* **Swagger UI (Docs):** `http://127.0.0.1:8000/docs`

---

## 🐳 4. Infrastructure (Docker)

To manage the PostgreSQL database container.

* **Start Database:**
```bash
docker-compose up -d

```


* **Stop Database:**
```bash
docker-compose down

```


* **View Logs:**
```bash
docker logs lazytrainer_db

```



### Database Troubleshooting

If you get a `type "vector" does not exist` error, run this to force enable the extension:

```powershell
docker exec -it lazytrainer_db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

```

---

## 📦 5. Dependency Management

We use `pip` to manage Python packages.

* **Install a new package:**
```bash
pip install package_name

```


* **Save dependencies (IMPORTANT):**
After installing anything, update the requirements file:
```bash
pip freeze > requirements.txt

```


* **Install from requirements (New setup):**
```bash
pip install -r requirements.txt

```



---

## 📂 6. Project Structure Reference

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
│   └── main.py             # App Entry Point (Router wiring)
├── alembic.ini             # Alembic Config
└── requirements.txt        # Dependencies

```
