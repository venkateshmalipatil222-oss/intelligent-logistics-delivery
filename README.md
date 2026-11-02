# Intelligent Logistics & Delivery Optimization Platform (ILDO)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![Pytest](https://img.shields.io/badge/Tests-54%20Passed-brightgreen?logo=pytest&logoColor=white)](./TESTING.md)

An enterprise-grade, full-stack logistics and autonomous delivery optimization system engineered with **FastAPI**, **React 19**, **MySQL 8.0**, and real-time **WebSockets**.

---

## 1. Architectural Highlights & Engineering Innovations

ILDO manages the complete end-to-end supply-chain delivery lifecycle:

```text
Customer Order → Warehouse Staging → Package Preparation → Multi-Factor Driver Allocation
       → Dijkstra / TSP Route Optimization → Real-Time WebSocket GPS Tracking
       → Dynamic ETA & Delay Risk Detection → Cryptographic OTP Proof-of-Delivery → Analytics
```

- **Multi-Factor Driver Assignment Engine**: Weighted fitness scoring matrix ($w_1 = 0.40$ distance, $w_2 = 0.25$ workload, $w_3 = 0.20$ rating, $w_4 = 0.15$ priority) with hard constraint payload and availability filtering.
- **Graph-Theoretic Route Optimization**: Dijkstra shortest path combined with Nearest-Neighbor Traveling Salesperson Problem (TSP) sequencing over geographic coordinates.
- **Real-Time Geolocation & Dynamic ETA Engine**: Browser Geolocation API streaming over authenticated WebSockets with traffic penalty factors and predictive delay risk detection.
- **Verifiable Proof of Delivery (PoD)**: Time-limited 6-digit cryptographic OTP verification with brute-force attempt lockout and structured delivery failure logging.
- **Enterprise Multi-Role Dashboards**: Dedicated experiences for System Administrators, Warehouse Managers, Fleet Drivers, and Customers.

---

## 2. Quick Start: Docker Compose (Single Command)

The entire platform (MySQL 8.0 database, FastAPI backend, and Nginx React frontend) can be spun up in a single command:

```bash
docker compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173) or [http://localhost](http://localhost)
- **FastAPI Backend & Healthcheck**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MySQL Database**: `localhost:3306` (`ildo_db`)

---

## 3. Local Development Setup

### Prerequisites
- Python 3.12+ (Python 3.13 tested)
- Node.js 18+ (Node 20+ tested)
- MySQL Server 8.0+

### Step 1: Environment Configuration
```bash
cp .env.example .env
```
Ensure your MySQL credentials and a secure 32+ character `SECRET_KEY` are configured.

### Step 2: Database Initialization & Migrations
```bash
# Run database schema migrations
alembic upgrade head

# Seed comprehensive enterprise demo dataset
python backend/seed_data.py
```

### Step 3: Backend Startup
```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 4: Frontend Startup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 4. Default Demo Credentials

All test accounts come pre-seeded with rich order histories, live tracking records, and inventory:

| Role | Email Address | Password | Focus & Capabilities |
|---|---|---|---|
| **System Administrator** | `admin@ildo.com` | `AdminPass123!` | System-wide KPI analytics, audit logs, fleet overview |
| **Warehouse Manager** | `manager@ildo.com` | `ManagerPass123!` | Bengaluru Hub, staging queues, auto-dispatch engine |
| **Warehouse Manager** | `manager.mumbai@ildo.com` | `ManagerPass123!` | Mumbai Hub distribution management |
| **Express Fleet Driver** | `driver@ildo.com` | `DriverPass123!` | Tata Ace EV van, live GPS tracking, OTP delivery |
| **Two-Wheeler Driver** | `driver2@ildo.com` | `DriverPass123!` | Ather 450X bike, quick urban parcel delivery |
| **Heavy Cargo Driver** | `driver3@ildo.com` | `DriverPass123!` | Tata Prima truck, bulk inter-city shipments |
| **Customer (Shipper)** | `customer@ildo.com` | `CustomerPass123!` | Order creation, live map tracking, cost estimator |
| **Enterprise Client** | `customer2@ildo.com` | `CustomerPass123!` | Corporate client, multi-package management |

---

## 5. Automated Testing Suite

The platform includes full-spectrum test coverage across database models, RBAC isolation, state machines, algorithms, and real-time tracking:

```bash
# Execute entire test suite
pytest -v backend/tests
```

**Verification Results**: `52 passed in 42.94s (100% pass rate)`

```text
tests/test_algorithms.py::5 PASSED                    [ 9%]
tests/test_analytics.py::6 PASSED                     [21%]
tests/test_auth.py::10 PASSED                         [40%]
tests/test_hardening_and_edge_cases.py::11 PASSED     [61%]
tests/test_health.py::6 PASSED                        [73%]
tests/test_logistics.py::4 PASSED                     [80%]
tests/test_pod_and_notifications.py::5 PASSED         [90%]
tests/test_tracking.py::5 PASSED                      [100%]
```

---

## 6. Complete Documentation Suite

- [**VIVA_PRESENTATION_GUIDE.md**](./VIVA_PRESENTATION_GUIDE.md) - **Academic viva defense manual**, mathematical formulas, live walkthrough script, and anticipated examiner questions & model answers.
- [**DEVELOPMENT_ROADMAP.md**](./DEVELOPMENT_ROADMAP.md) - Execution progress and deliverables across all 9 completed development phases.
- [**PROJECT_ARCHITECTURE.md**](./PROJECT_ARCHITECTURE.md) - Multi-tier software architecture, micro-component designs, and security boundaries.
- [**DATABASE_DESIGN.md**](./DATABASE_DESIGN.md) - Relational entity schemas, 3NF normalization, foreign key constraints, and indexing strategy.
- [**AI_AND_OPTIMIZATION_DESIGN.md**](./AI_AND_OPTIMIZATION_DESIGN.md) - Mathematical formulation for driver scoring, Dijkstra's algorithm, TSP sequencing, and dynamic ETA estimation.
- [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md) - Complete REST endpoint catalog and WebSocket real-time protocol specification.
- [**TESTING.md**](./TESTING.md) - Test architecture, transactional isolation fixtures, regression checks, and edge-case test plan.
