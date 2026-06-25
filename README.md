# Moola - Intelligent & Collaborative Bookkeeping System

[简体中文](README_zh.md) | **English**

Moola is a premium, modern, and interactive bookkeeping application designed for both individual personal finance tracking and collaborative group/project bookkeeping (e.g. shared apartment expenses, travel costs, team budgets).

---

## 🚀 Key Features

* **Personal Ledger**: Manage daily income and expenses with high visual clarity. Supports auto-formatting for large transactions (e.g., displaying `W` for 100K+ amounts with hover tooltips).
* **Collaborative Project Ledger**: Share book keeping records with group members, view settlements, and manage group expenses collectively.
* **Smart Category Management**: Supports default system categories (food, shopping, travel, salary, etc.) and custom user-created categories with curated color themes and modern Lucide icons.
* **Multiple Image Uploads**: Attach up to 6 receipt photos or screenshots per bookkeeping record.
* **Premium Gallery Viewer**: Fully-featured image preview modal with drag-to-pan, zoom (mouse scroll or mobile pinch gestures), rotation, mirroring, quick download, and copy image URL actions.
* **Optimized HTTP Caching**: Features `Cache-Control` max-age caching (1 year) and dynamic conditional validation using `ETag` (`If-None-Match` yielding `304 Not Modified`) for images.
* **Auto-expiring Database Cache (TTL)**: Restricts database size by maintaining a 30-day MongoDB Time-To-Live (TTL) index on file access times. Viewing files automatically renews their 30-day lease.

---

## 🛠️ Technology Stack

* **Frontend**: Vue 3 (Composition API), Vite, Element Plus, Pinia (State Management), Vue Router, TailwindCSS / Vanilla CSS, Lucide Vue Icons.
* **Backend**: FastAPI (Python 3.11+), Motor (Async MongoDB Driver), Pydantic (V2), PyJWT, python-multipart.
* **Database**: MongoDB (6.0+).

---

## 🐳 Option 1: One-Click Docker Compose Deployment (Recommended)

This is the easiest way to deploy the entire stack (Frontend, Backend, and MongoDB) onto a cloud server or local machine. Ports inside the container are automatically aligned with the host.

### 1. Configure Ports
Create a `.env` file in the project root directory (next to `docker-compose.yml`):
```env
FRONTEND_PORT=9090
BACKEND_PORT=9080
```

### 2. Deploy Services
Run the following command in the project root directory:
```bash
docker compose up --build -d
```

### 3. Verify & Access
* **Web UI (Frontend)**: Access the system at `http://<YOUR_SERVER_IP>:9090`.
* **API (Backend)**: Exposes endpoints internally, and is proxied through port `9090/api` using Nginx.
* **Database (MongoDB)**: Running on port `27017` on the host (with data persisted in `mongo_data` volume).

*(Note: Ensure your cloud server security group opens port `9090` and `9080` if you need direct backend access. Only port `9090` is required for standard application usage).*

---

## 💻 Option 2: Standalone Local Setup (Manual)

If you wish to run the backend and frontend separately for development, follow these steps.

### Prerequisites
* **MongoDB**: Installed and running on `mongodb://localhost:27017`.
* **Python**: Version 3.11+.
* **Node.js**: Version 18.0+.

---

### Step A: Backend Setup

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   Create a `backend/.env` file:
   ```env
   PROJECT_NAME=Moola
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=moola_db
   JWT_SECRET=super-secret-key-moola-bookkeeping-app-2026
   ACCESS_TOKEN_EXPIRE_DAYS=30
   JWT_ALGORITHM=HS256
   HOST=0.0.0.0
   PORT=8000
   RELOAD=True
   ```

5. **Run the API server**:
   ```bash
   python main.py
   ```
   The backend API will run on `http://localhost:8000`. Database indexes and system categories will be automatically preloaded on startup.

---

### Step B: Frontend Setup

1. **Navigate to the frontend folder**:
   ```bash
   cd frontend
   ```

2. **Install node modules**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   Create a `frontend/.env` file:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```
   The frontend UI will run on `http://localhost:5173`.

5. **Build for production**:
   ```bash
   npm run build
   ```
   The static distribution files will be output to the `dist/` directory, which can be served using any static web server (such as Nginx).
