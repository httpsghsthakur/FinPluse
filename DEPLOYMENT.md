# Deploying Finpluse as a Single Unified Service on Render

Both the **React 19 Frontend** and **FastAPI Python Backend** run together on the **same Render Web Service instance** under a single URL and port.

---

## Why Single-Service Deployment?

- ✅ **1 Service Instead of 2**: Saves free-tier quota on Render.
- ✅ **Zero CORS Configuration**: Frontend and API share the exact same domain (`https://your-app.onrender.com`).
- ✅ **Fast Cold Starts**: Only 1 service spins up instead of 2 separate instances.
- ✅ **Built-in SPA Routing**: FastAPI serves the React Single Page App for all client URLs (`/dashboard`, `/copilot`, `/simulator`, etc.) and handles REST API routes on `/api/v1/*`.

---

## 1-Click Deployment with Render Blueprint

1. Go to **[dashboard.render.com](https://dashboard.render.com)**.
2. Click **New +** (top right) → Select **Blueprint**.
3. Connect your GitHub repository: **[https://github.com/httpsghsthakur/Finpluse](https://github.com/httpsghsthakur/Finpluse)**.
4. Render automatically reads `render.yaml` and prepares the unified `finpluse` service.
5. Click **Apply**.

---

## Manual Setup on Render (Web Service)

If configuring manually without Blueprints:

1. Click **New +** → **Web Service** → Connect `https://github.com/httpsghsthakur/Finpluse`.
2. Configure settings:
   - **Name**: `finpluse`
   - **Region**: Any (e.g. `Oregon (US West)`)
   - **Root Directory**: _(Leave blank)_
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     npm install && npm run build && cd backend && pip install --upgrade pip && pip install --prefer-binary -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
3. Add **Environment Variables**:
   | Key              | Value                                       |
   | :--------------- | :------------------------------------------ |
   | `PYTHON_VERSION` | `3.11.9`                                    |
   | `NODE_VERSION`   | `20.14.0`                                   |
   | `ENVIRONMENT`    | `production`                                |
   | `DEBUG`          | `false`                                     |
   | `SEED_DEMO_DATA` | `true`                                      |
   | `DATABASE_URL`   | `sqlite+aiosqlite:///./finpluse.db`         |
   | `SECRET_KEY`     | _(Click "Generate" or enter random string)_ |
4. Click **Create Web Service**.

---

## Accessing Your App

Once Render finishes building:

- 🌐 **Web App & Dashboard**: `https://<your-app-name>.onrender.com/`
- 💬 **AI Copilot**: `https://<your-app-name>.onrender.com/copilot`
- 📊 **Simulator**: `https://<your-app-name>.onrender.com/simulator`
- 📚 **Swagger API Docs**: `https://<your-app-name>.onrender.com/docs`
- 🩺 **Health Check**: `https://<your-app-name>.onrender.com/health`

---

## Self-Hosting with Docker Compose

Finpluse is packaged as a unified container and published to GitHub Container Registry (GHCR). You can easily run the app and its required PostgreSQL database on any server using Docker Compose.

### 1. Requirements
- Docker & Docker Compose installed.

### 2. Run the Stack
Simply run the following command in the directory containing docker-compose.yml:
\\\ash
docker-compose up -d
\\\

The stack will:
1. Pull the official ghcr.io/httpsghsthakur/finpluse:latest image.
2. Spin up a postgres:15-alpine database.
3. Automatically connect the app to the database.

### 3. Access the App
Navigate to http://localhost:8000 in your browser. The single container serves both the React frontend and the FastAPI backend!
