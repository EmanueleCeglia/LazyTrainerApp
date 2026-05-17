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
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL_NAME=gpt-4o-mini
```

---

## 🗄️ 2. Database Management (Alembic)

We use **Alembic** for database migrations (User Profiles and Workout Plans). Never modify the PostgreSQL schema manually. Use this workflow when you change `models.py`.

### A. The Migration Workflow

1. **Modify** your `models.py` file.
2. **Generate** a migration script (snapshot):
```bash
cd backend
alembic revision --autogenerate -m "Describe your change here"
```

3. **🔍 CRITICAL: Review the File**
* Go to `backend/alembic/versions/` and open the new file.
* **Check logic:** Ensure the SQL commands look correct.

4. **Apply** the changes to the Database:
```bash
alembic upgrade head
```

### B. Undo/Reset Changes

* **Undo last migration:** `alembic downgrade -1`
* **Hard Reset (If corrupted):**
1. Open PgAdmin Query Tool.
2. Run: `DROP TABLE IF EXISTS alembic_version;` (plus other tables like `users`, `workout_plans`).
3. Re-run: `alembic upgrade head`

---

## 🌱 3. Data Storage

### A. Exercise Catalog (JSON)
**All exercises are stored statically in `backend/src/data/exercises.json`.**

* **Adding Exercises:** Simply add a new JSON object to the `exercises.json` file. The backend will automatically read it.
* **No Seeding Required:** You do not need to run any seeding scripts or generate embeddings.

### B. Fitness Rulebook (Markdown)
**The AI's fitness knowledge lives in `backend/src/ai/fitness_rules.md`.**

This file is injected directly into the Strategist LLM prompt at generation time. It contains:
* **Split selection rules** based on experience level and training days (e.g., Beginner → Full Body, Intermediate → PPL).
* **Training methodology** based on user goals (e.g., Strength → 4x6-8 heavy, Weight Loss → HIIT).

To update the AI's fitness philosophy, simply edit this markdown file. No code changes required.

---

## 🚀 4. Running the Server

To start the FastAPI server with **hot-reload** and accessible from mobile devices:

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

* **API URL:** `http://YOUR_LAN_IP:8000`
* **Swagger UI (Docs):** `http://YOUR_LAN_IP:8000/docs`

### Frontend (React Native)

```bash
cd frontend
npm install    # First time only
npx expo start
```

> **Important:** Update the `API_BASE_URL` in `frontend/src/api/client.ts` to match your computer's LAN IP address.

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

### Backend (Python)
* **Install package:** `pip install package_name`
* **Save dependencies:** `pip freeze > requirements.txt`
* **Install from requirements:** `pip install -r requirements.txt`

### Frontend (Node.js)
* **Install package:** `npm install package_name`
* **Install all dependencies:** `npm install`

---

## 📂 7. Project Structure Reference

```text
backend/
├── alembic/                    # Migration scripts
├── src/
│   ├── api/                
│   │   ├── routes.py           # API Endpoints (Generate, Swap, Adjust, Restructure, BulkSwap)
│   │   └── schemas.py          # Pydantic Models (Input/Output Validation)
│   ├── ai/                     # 🧠 THE BRAIN (Custom Pipeline)
│   │   ├── pipeline.py         # WorkoutPipeline, WorkoutModifier, BulkExerciseSwapper
│   │   └── fitness_rules.md    # Expert Fitness Rulebook (Knowledge Base)
│   ├── data/           
│   │   └── exercises.json      # Curated static exercise catalog
│   ├── database/           
│   │   ├── connection.py       # DB Session
│   │   └── models.py           # SQL Tables (UserProfile w/ experience_level, WorkoutPlan)
│   └── main.py                 # App Entry Point
├── .env                        # Secrets (API Keys) - NOT IN GIT
├── alembic.ini                 # Alembic Config
└── requirements.txt            # Dependencies

frontend/
├── App.tsx                     # Root Component (Theme, State, Routing)
├── src/
│   ├── api/client.ts           # API Client (generate, restructure, bulkSwap)
│   ├── components/Button.tsx   # Reusable Button Component
│   ├── screens/
│   │   ├── QuestionnaireScreen.tsx  # User Input (Goals, Level, Equipment, etc.)
│   │   └── WorkoutScreen.tsx       # Plan Display, Edit Mode, Split Change
│   └── styles/
│       ├── theme.ts            # Design Tokens (colors, spacing, borderRadius)
│       └── ThemeContext.tsx     # Dark/Pink Mode Provider
├── app.json                    # Expo Configuration
└── package.json                # Node Dependencies
```

---

## ⚙️ 8. Core Workflows & Logic

### A. The 3-Step Pipeline Architecture (Creation)

When `/generate` is called, a **WorkoutPipeline** executes sequentially:

1. **Strategist (LLM):** Analyzes User Profile (Biometrics, Goals, Experience Level, Days) + reads `fitness_rules.md` → Outputs a "Weekly Skeleton" (Split type, target zones, methods).
2. **Selector (Python):** Takes Skeleton + Equipment → Queries the `exercises.json` catalog using strict Python logic → Outputs Specific Exercises.
3. **Coach (LLM):** Takes Exercises → Applies Science (Sets/Reps) based on goals → Formats the final JSON plan with a funny animal-themed name.

### B. The Modifier System (Adaptation)

For small changes, we do NOT run the full pipeline. We use specialized agents:

* **Swap Exercise (`PUT /plans/{id}/swap`):** Uses Python logic to find a biomechanical equivalent within the JSON, then uses an LLM to format the new sets/reps.
* **Bulk Swap (`POST /plans/{id}/bulk-swap`):** `BulkExerciseSwapper` agent handles multiple exercise replacements across different days. It matches target zones and force types, avoids duplicates, and uses a single LLM call to assign coherent parameters for all replacements.
* **Adjust Difficulty (`PUT /plans/{id}/adjust`):** Uses an LLM to rewrite Sets/Reps/Methods for specific exercises based on user feedback.

### C. Restructure Split (`POST /plans/{id}/restructure`)

* **Logic:** Extracts all existing exercises into a "pool", then runs the full pipeline with a `force_split` override. The Selector pulls from the pool first (preserving favorites) before fetching new exercises from the catalog.

### D. Progression (The "Next" Block)

* **Endpoint:** `POST /generate/next`
* **Logic:** Reads the *previous* `WorkoutPlan` from the database, retrieves the user's biometrics, processes User Feedback, and feeds this rich history into the **Strategist** to evolve the program natively (Progressive Overload).

---

## 🧠 9. Troubleshooting

### Common Issues

* **JSON Parsing Errors**:
  * *Cause:* The LLM might occasionally return malformed JSON or markdown wrappers (```json ... ```).
  * *Fix:* The endpoints utilize `clean_json_string` or Pydantic models to strictly enforce JSON validation.

* **"No substitute found" / Empty Exercise Lists**:
  * *Cause:* The `Selector` Python logic is too strict, and the required combination of `equipment`, `target_zone`, and `force_type` does not exist in `exercises.json`.
  * *Fix:* Ensure `exercises.json` has sufficient variety, or relax the Python fallback logic inside `filter_exercises()` in `pipeline.py`.

* **TypeError during Adjustments/Swaps**:
  * *Cause:* The `schedule` JSON structure contains top-level keys that aren't dictionaries (like `plan_name`), which iterators fail on.
  * *Fix:* Ensure all iterators in `routes.py` use `isinstance(week, dict)` before checking for `day_name`.

* **Frontend can't connect to Backend**:
  * *Cause:* The `API_BASE_URL` in `frontend/src/api/client.ts` doesn't match your computer's LAN IP.
  * *Fix:* Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) and update the IP address.

* **Database column does not exist**:
  * *Cause:* A new column was added to `models.py` but the migration hasn't been applied.
  * *Fix:* Run `alembic revision --autogenerate -m "description"` then `alembic upgrade head`.