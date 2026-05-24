# 🏋️ The Lazy Trainer: Master Guide

This document contains everything you need to know to setup, develop, test, and distribute your AI fitness app.

---

## 🏗️ Architecture Overview

Your app is divided into three main components:
1. **The Database:** PostgreSQL running inside a Docker container.
2. **The Backend:** A Python FastAPI server. It runs the AI pipeline, generates workouts, handles authentication, and saves data.
3. **The Frontend:** A React Native app built with Expo. It contains the UI and sends network requests to the Backend.

Our `client.ts` file automatically switches network routes depending on how you start the app:
- **Development Mode (`__DEV__ = true`):** Connects to your local Wi-Fi IP (`10.107.17.6:8000`).
- **Production Mode (`__DEV__ = false`):** Connects to the public Localtunnel URL (`https://lazytrainer-api.loca.lt`).

---

## 🛠️ Part 1: First-Time Setup (Developer)
If you are pulling this code for the first time, you must follow these steps to configure your environment.

### 1. Start the Database
Open **Docker Desktop**, then open a terminal in the main folder and run:
```bash
docker-compose up -d
```

### 2. Configure Secrets (.env)
Create a `.env` file in the `backend/` folder. **Do not commit this to GitHub.**
```ini
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/postgres
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL_NAME=gpt-5.4-mini
SECRET_KEY=super-secret-key-for-lazytrainer-replace-in-prod
```

### 3. Initialize the Backend
Open a terminal in `backend/`:
```bash
# Activate your virtual environment
venv\Scripts\activate

# Apply database migrations
alembic upgrade head
```

---

## 📱 Part 2: Development Mode (Testing Locally)
Use this mode when you are coding, building new features, or just want to test the app quickly on your own phone.

**1. Start the Backend**
Open a terminal in the `backend` folder and run:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**2. Start the Frontend**
Open a second terminal in the `frontend` folder and run:
```bash
npx expo start
```

**3. Test on your Phone**
Open the **Expo Go** app on your phone and scan the QR code that appears in the frontend terminal. You are now testing live!

---

## 🚀 Part 3: Production Mode (Building for Friends)
Use this mode when you want to compile an `.apk` file so your friends can install the app on their Android phones permanently.

### Step A: Build the APK
*You only need to do this if you changed the React Native code in the `frontend` folder.*
1. Open a terminal in the `frontend` folder.
2. Ensure you are logged in (`npx eas-cli login`).
3. Run the cloud build command:
```bash
npx eas-cli build -p android --profile preview
```
4. When it finishes, it will give you a link to an `.apk` file. Send this link to your friends!

### Step B: The "Server-On" Checklist
Because your laptop is acting as the server, your friends cannot log in or generate workouts unless your laptop is awake and listening. Whenever they want to use the app, you must do two things:

1. **Start the Backend:**
   ```bash
   cd backend
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```
2. **Open the Internet Bridge:**
   ```bash
   lt --port 8000 --subdomain lazytrainer-api
   ```
*(Keep both terminals open! Your friends can now use the app from anywhere in the world).*

---

## 📊 Part 4: Database Administration
You can watch your friends create accounts and generate workouts in real-time.

1. Open **pgAdmin 4**.
2. Connect to the Server:
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Maintenance DB:** `postgres`
   - **Username:** `postgres`
   - **Password:** `password`
3. In the left menu, go to: `Databases` -> `postgres` -> `Schemas` -> `public` -> `Tables`.
4. Right-click on `users` or `workout_plans` and select **View/Edit Data** -> **All Rows**.
5. Press the **Play (▶️) / Refresh** button at the top of the data grid to reload the table and see new data instantly!

---

*For detailed architectural documentation and AI pipeline breakdowns, see `DEVELOPER_GUIDE.md`.*