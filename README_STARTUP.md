# 🚀 LazyTrainer Startup Guide

This guide provides the exact steps to boot up the entire LazyTrainer stack from scratch. The application consists of three main parts:
1. **The Database** (PostgreSQL running in Docker)
2. **The Backend** (FastAPI / Python)
3. **The Frontend** (React Native / Expo)

---

## Step 1: Start the Database (Docker)
Before the backend can run, it needs the database to be active.

1. Open **Docker Desktop** on your computer and make sure the engine is running.
2. Open a terminal in the main `LazyTrainer` folder.
3. Run the following command to start the database in the background:
   ```powershell
   docker-compose up -d
   ```

---

## Step 2: Configure Secrets (.env)
Create a file named `.env` inside the `backend/` directory. **This file must NEVER be committed to GitHub.**

```ini
# Database Connection
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/postgres

# AI Provider
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL_NAME=gpt-5.4-mini
```

> ⚠️ **IMPORTANT:** Replace `your-openai-api-key-here` with your actual OpenAI API key. The `.gitignore` is already configured to exclude this file.

---

## Step 3: Start the Backend (FastAPI)
The backend handles the AI generation and saves profiles to the database.

1. Open a **new terminal** and navigate to the backend folder:
   ```powershell
   cd LazyTrainer\backend
   ```
2. Activate your Python virtual environment:
   ```powershell
   .\venv\Scripts\activate
   ```
   *(You should see `(venv)` appear in your terminal).*
3. Install dependencies (first time only):
   ```powershell
   pip install -r requirements.txt
   ```
4. Run database migrations (first time or after schema changes):
   ```powershell
   alembic upgrade head
   ```
5. Start the Python server. **Use `--host 0.0.0.0`** so your phone can connect:
   ```powershell
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
6. **Verification:** You should see `Uvicorn running on http://0.0.0.0:8000`. Leave this terminal open!

---

## Step 4: Configure Frontend API URL
Before starting the frontend, update the backend URL to match your computer's local IP.

1. Find your computer's LAN IP address:
   ```powershell
   ipconfig
   ```
   Look for `IPv4 Address` under your active network adapter (e.g., `192.168.1.100` or `10.x.x.x`).

2. Open `frontend/src/api/client.ts` and update the IP:
   ```typescript
   export const API_BASE_URL = 'http://YOUR_IP_HERE:8000';
   ```

> 💡 This step is needed because physical phones cannot access `localhost`. They need your computer's actual network IP.

---

## Step 5: Start the Frontend (React Native / Expo)
The frontend is the mobile app UI that communicates with the backend.

1. Open a **new, third terminal** and navigate to the frontend folder:
   ```powershell
   cd LazyTrainer\frontend
   ```
2. Install dependencies (first time only):
   ```powershell
   npm install
   ```
3. Start the Expo development server:
   ```powershell
   npx expo start
   ```
4. A QR code will appear in your terminal.

---

## Step 6: Open the App on Your Device

### Option A: Physical Phone (Recommended)
1. Install **Expo Go** from the Google Play Store or Apple App Store.
2. Scan the QR code shown in the terminal with your phone's camera.
3. The app will open directly on your device!

### Option B: Android Emulator
1. Open **Android Studio** and launch an emulator from the Device Manager.
2. In the Expo terminal, press the **`a`** key.
3. Expo will install and launch the app on the emulator automatically.

> **💡 Emulator Note:** If using the emulator, change `API_BASE_URL` in `client.ts` to `http://10.0.2.2:8000` (the emulator's alias for your computer's localhost).

---

## ✅ Summary

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `docker-compose up -d` | Start PostgreSQL database |
| 2 | `uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload` | Start backend API |
| 3 | `npx expo start` | Start React Native frontend |
