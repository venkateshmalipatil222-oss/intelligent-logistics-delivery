# Testing Strategy & Execution Guide

---

## 1. Testing Philosophy
In accordance with Rule 30 of the ILDO project charter:
> **"Use an isolated test database. Never run tests against the user's production database. Never claim all tests pass without executing them. Report executed, passed, failed, and skipped test counts."**

All automated Pytest suites run against an ephemeral, in-memory SQLite database (`sqlite:///:memory:`) using SQLAlchemy's `StaticPool`. This completely isolates testing logic from the live MySQL database (`ildo_db`) and prevents data corruption, pollution, or accidental table drops.

---

## 2. Test Execution Command

Run the complete test suite:
```bash
pytest -v backend/tests
```

Run with execution timing and captured warnings:
```bash
pytest -v --durations=5 backend/tests
```

---

## 3. Test Fixture Architecture (`backend/tests/conftest.py`)

1. **`setup_test_db` (Session-scoped)**: Builds the complete schema once in the in-memory SQLite engine and tears it down after tests complete.
2. **`db_session` (Function-scoped)**: Starts a nested transaction before each individual test and rolls it back upon exit, ensuring 100% test isolation.
3. **`client` (Function-scoped)**: Wraps FastAPI `TestClient` with dependency overrides on `get_db`.

---

## 4. Phase 1 Verified Test Cases

| Test Name | File | Description | Status |
|---|---|---|---|
| `test_root_endpoint` | `test_health.py` | Validates root status, version, and documentation links. | PASSED |
| `test_health_ping` | `test_health.py` | Validates lightweight `/ping` endpoint. | PASSED |
| `test_comprehensive_health` | `test_health.py` | Validates database connectivity, latency calculation, and process metrics. | PASSED |
| `test_password_hashing_and_verification` | `test_health.py` | Validates bcrypt salting, hashing, and matching. | PASSED |
| `test_jwt_token_lifecycle` | `test_health.py` | Validates token creation, claims encoding, and signature decoding. | PASSED |
| `test_jwt_token_invalid_signature` | `test_health.py` | Validates that tampered tokens trigger cryptographic rejection. | PASSED |

Total Phase 1 Tests: **6 Executed, 6 Passed, 0 Failed, 0 Skipped**.
