# Intelligent Logistics & Delivery Optimization Platform (ILDO)

A full-stack, enterprise-grade logistics and autonomous delivery optimization system engineered with Python (FastAPI), React, MySQL, and real-time WebSockets.

---

## 1. Project Overview & Vision
ILDO manages the complete end-to-end delivery lifecycle:
```text
Customer Order → Warehouse Processing → Package Preparation → Driver & Fleet Assignment
       → Route Optimization → Real-Time GPS Tracking → Dynamic ETA Calculation
       → Delay Risk Detection → Delivery Completion → Proof of Delivery (OTP) → Analytics
```

### Key Differentiators (No Simulated or Fake Outputs)
- **Multi-Factor Driver Assignment Engine**: Evaluates driver proximity, live workload, vehicle capacity compatibility, priority, and historical on-time rates with hard constraint rejection.
- **Route Optimization Engine**: Dijkstra shortest path combined with Nearest-Neighbor multi-stop sequencing over true geographic coordinates.
- **Real-Time Geolocation Tracking**: Uses the browser/device Geolocation API streamed over authenticated WebSockets.
- **Dynamic ETA & Delay Risk Detection**: Combines distance, calibrated speeds, service times, and uncertainty buffers to alert before delays occur.
- **Verifiable Proof of Delivery**: Time-limited cryptographic OTP and digital confirmation.

---

## 2. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS v4, Lucide React, Axios, Leaflet, Recharts |
| **Backend** | Python 3.13, FastAPI, Uvicorn, SQLAlchemy 2.0, Alembic, Pydantic V2, WebSockets |
| **Database** | MySQL 8.0 / 26.7 (`ildo_db`) with PyMySQL pooling; isolated in-memory SQLite for automated tests |
| **Security** | Passlib bcrypt (salt rounds = 12), PyJWT (HS256), Role-Based Access Control |
| **Testing** | Pytest 9.x with transactional fixtures and zero production database impact |

---

## 3. Quick Start & Local Setup

### Prerequisites
- Python 3.12+ (Python 3.13 tested)
- Node.js 18+ (Node 26 tested)
- MySQL Server 8.0+

### Step 1: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your MySQL credentials and a secure 32+ character `SECRET_KEY` are configured.

### Step 2: Backend Setup & Startup
```bash
# In project root:
# Install dependencies
python -m pip install -r backend/requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Interactive API docs are available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
Direct healthcheck endpoint: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Step 3: Frontend Setup & Startup
```bash
# In frontend directory:
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 4. Running Automated Tests
```bash
# Run backend pytest suite:
pytest -v backend/tests
```

---

## 5. System Documentation Suite
- [PROJECT_ARCHITECTURE.md](./PROJECT_ARCHITECTURE.md) - System architecture, request flows, and security boundaries.
- [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) - Entity relationship models, constraints, and indexes.
- [AI_AND_OPTIMIZATION_DESIGN.md](./AI_AND_OPTIMIZATION_DESIGN.md) - Algorithm formulas, weights, and routing models.
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - REST and WebSocket schemas.
- [TESTING.md](./TESTING.md) - Test setup, coverage, and test fixtures.
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - Multi-phase execution plan.
