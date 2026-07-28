# Self-RAG Project

This document contains all the necessary commands to start and stop your Self-RAG application.

## Quick Start (The Easy Way)

I have created two scripts for you to make starting and stopping the project as easy as double-clicking a file:

- **`start.bat`**: Double-click this to start Docker, the backend, and the frontend all at once in separate windows.
- **`stop.bat`**: Double-click this to gracefully shut down the Docker databases.

---

## Manual Commands

If you prefer to run things manually in your own terminal windows, here are the commands you need:

### 1. Start the Databases (Docker)
Open a terminal in the `d:\self-rag` folder and run:
```powershell
docker compose up -d
```
*(This starts PostgreSQL and Qdrant in the background)*

### 2. Start the Backend API
Open a **new** terminal, navigate to the backend folder, and start the server:
```powershell
cd d:\self-rag\backend
uv run uvicorn api.main:app --reload
```

### 3. Start the Frontend UI
Open a **new** terminal, navigate to the frontend folder, and start the React app:
```powershell
cd d:\self-rag\frontend
npm run dev
```

### 4. Stop the Databases (Docker)
When you are completely done working and want to free up memory, open a terminal in `d:\self-rag` and run:
```powershell
docker compose down
```
*(You can just press CTRL+C in the backend and frontend terminals to stop them)*

---

## Database Credentials

If you ever need to connect to your PostgreSQL database directly (using DBeaver, pgAdmin, or psql), here are the credentials:

- **Host:** `localhost`
- **Port:** `5433`
- **Database Name:** `self_rag_v2`
- **Username:** `user_v2`
- **Password:** `password_v2`
