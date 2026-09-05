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
OPENAI_MODEL_NAME=gpt-5.4-mini

# Auth
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 days

# Optional
SQL_ECHO=false                      # true logs every SQL statement
```

**`src/config.py` is the only place these are read.** Nothing in the codebase
hardcodes a database URL, model name or secret - if you need a new setting, add it
there rather than calling `os.getenv` from a module.

Alembic reads `DATABASE_URL` from the same place (`alembic/env.py` overrides the
`sqlalchemy.url` in `alembic.ini`), so migrations can never target a different
database than the app.

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

Every entry must carry all eight keys:

```json
{
  "name": "Chest Press Machine",
  "target_zone": "Upper",          // Upper | Lower | Core
  "force_type": "Push",            // Push | Pull | Squat | Hinge | Lunge | Dynamic | Static
  "muscle_group": "Chest",
  "secondary_muscles": ["Triceps", "Front Delts"],
  "mechanics": "Compound",         // Compound | Isolation
  "equipment": ["Machine"],
  "instructions": "..."
}
```

#### ⚠️ The taxonomy invariant
`force_type` and `mechanics` are not independent. The Coach sequences a day using
the 5-tier hierarchy in `coach_rules.md`, which keys entirely off `force_type`:

> **An exercise with `"mechanics": "Isolation"` must use `force_type` `Dynamic` or `Static`.**
> `Push`, `Pull`, `Squat`, `Hinge` and `Lunge` are reserved for multi-joint compounds.

Breaking this has two consequences: the Selector fills a compound slot with an
isolation lift (a cable fly satisfying the day's "Push"), and the Coach sequences a
bicep curl as a Tier 2 primary. Keep `equipment` values spelled exactly as they
appear in `LOCATION_EQUIPMENT` (`routes.py`) and in the questionnaire.

### B. Fitness Rulebooks (Markdown)
**The AI's fitness knowledge lives in two files, one per LLM stage.** Each is read
at generation time and injected into that stage's prompt.

| File | Feeds | Contains |
| --- | --- | --- |
| `backend/src/ai/strategist_rules.md` | Stage 1 (Strategist) | The Master Split Matrix (days x experience level), the Time-to-Exercise map, the muscle-to-`force_type` mapping, and Goal-to-Method mapping |
| `backend/src/ai/coach_rules.md` | Stage 3 (Coach) | Sets/reps/rest/intensity per method, and the 5-Tier Master Sequencing Hierarchy |

To update the AI's fitness philosophy, edit the relevant markdown file. No code
changes required. If you change the vocabulary in `strategist_rules.md` (zones or
force types), `exercises.json` must use the same words - the Python Selector matches
them literally.

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

> **Important:** Set your LAN IP in `frontend/.env` (copy `frontend/.env.example`):
>
> ```ini
> EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:8000
> ```
>
> Expo inlines any `EXPO_PUBLIC_*` variable at build time, so this no longer needs a
> code change. `client.ts` still falls back to its baked-in dev/prod URLs when the
> variable is absent - which is what an EAS build gets, since `.env` is gitignored.

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
│   ├── config.py               # ⚙️ ALL environment settings (single source of truth)
│   ├── api/
│   │   ├── routes.py           # API Endpoints (Generate, Swap, Adjust, Restructure, BulkSwap)
│   │   ├── auth.py             # JWT issue/verify + bcrypt hashing
│   │   ├── auth_routes.py      # /auth/register, /auth/login
│   │   └── schemas.py          # Pydantic Models (Input/Output Validation)
│   ├── ai/                     # 🧠 THE BRAIN (Custom Pipeline)
│   │   ├── pipeline.py         # WorkoutPipeline, WorkoutModifier, BulkExerciseSwapper
│   │   ├── strategist_rules.md # Stage 1 knowledge: splits, volume, force mapping
│   │   └── coach_rules.md      # Stage 3 knowledge: sets/reps + sequencing tiers
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
│   ├── context/AuthContext.tsx # Token storage + auto-logout on 401
│   ├── screens/
│   │   ├── AuthScreen.tsx           # Login / Register
│   │   ├── QuestionnaireScreen.tsx  # User Input (Goals, Level, Equipment, etc.)
│   │   └── WorkoutScreen.tsx       # Plan Display, Edit Mode, Split Change
│   └── styles/
│       ├── theme.ts            # Design Tokens (colors, spacing, borderRadius)
│       └── ThemeContext.tsx     # Dark/Pink Mode Provider
├── .env                        # EXPO_PUBLIC_API_URL - NOT IN GIT
├── .env.example                # Template for the above
├── app.json                    # Expo Configuration
├── eas.json                    # EAS Build profiles
└── package.json                # Node Dependencies
```

---

## 🔐 8. Authentication & Plan Ownership

Every endpoint except `GET /` and `/auth/*` requires a Bearer token.

* **Register/Login** issue an HS256 JWT whose `sub` claim is the username.
  Passwords are bcrypt-hashed and clamped to bcrypt's 72-**byte** limit.
* `get_current_user` resolves that token back to a `UserProfile` row.

### The ownership rule
`WorkoutPlan.user_id` always holds the **owner's username, written server-side from
the JWT**. Requests still accept a `user_id` field so older app builds keep working,
but it is ignored everywhere.

Every plan-scoped handler fetches through one helper:

```python
plan = get_owned_plan(plan_id, db, current_user)
```

which filters on `id AND user_id` and raises **404** (not 403) on a miss, so a plan
belonging to someone else is indistinguishable from one that does not exist. If you
add a new `/plans/{plan_id}/...` endpoint, route it through this helper - a plain
`db.query(WorkoutPlan).filter(WorkoutPlan.id == plan_id)` is a security bug.

### Reading plans back
| Endpoint | Purpose |
| --- | --- |
| `GET /plans` | Every plan the caller owns, newest first (summary rows) |
| `GET /plans/{plan_id}` | One plan including the full `schedule` |

The app calls both on launch to restore the most recent program, so a logout no
longer loses your plan.

---

## ⚙️ 9. Core Workflows & Logic

### A. The 3-Step Pipeline Architecture (Creation)

When `/generate` is called, a **WorkoutPipeline** executes sequentially:

1. **Strategist (LLM):** Analyzes User Profile (Biometrics, Goals, Experience Level, Days) + reads `strategist_rules.md` → Outputs a "Weekly Skeleton" (Split type, target zones, methods).
2. **Selector (Python):** Takes Skeleton + Equipment → Queries the `exercises.json` catalog using strict Python logic → Outputs Specific Exercises.
3. **Coach (LLM):** Takes Exercises + reads `coach_rules.md` → Applies Science (Sets/Reps) and reorders each day by the sequencing tiers → Formats the final JSON plan with a funny animal-themed name.

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

## 🧠 10. Troubleshooting

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
  * *Cause:* `EXPO_PUBLIC_API_URL` is unset or points at the wrong LAN IP.
  * *Fix:* Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) and set it in `frontend/.env`. Restart `npx expo start` afterwards - env vars are inlined at bundle time.

* **404 "Plan not found" on a plan you can see**:
  * *Cause:* The plan is owned by a different username. Ownership is enforced on every plan endpoint.
  * *Fix:* Log in as the owner. Plans created before this rule existed were stamped with a random `user_id` and are unreachable - regenerate them.

* **401 on every request after a week**:
  * *Cause:* JWTs expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (7 days by default).
  * *Fix:* Nothing to do - the app now logs out automatically and shows the login screen.

* **A "Push" day comes back full of cable flies and curls**:
  * *Cause:* An exercise in `exercises.json` violates the taxonomy invariant (see §3A) - an `Isolation` tagged with a compound `force_type`.
  * *Fix:* Retag it as `Dynamic`.

* **Database column does not exist** (e.g. `users.hashed_password`):
  * *Cause:* A new column was added to `models.py` but the migration hasn't been applied.
  * *Fix:* Run `alembic upgrade head`. If you need a brand-new migration, `alembic revision --autogenerate -m "description"`, review it, then upgrade.
  * *Note:* Databases created with `reset_db.py` were never stamped by Alembic. Run `alembic stamp head` on those, or drop and rebuild with `alembic upgrade head`.