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

---

## 3. Verified Automated Test Suite (16 Executed, 16 Passed)

### Authentication & RBAC Suite (`backend/tests/test_auth.py`)
| Test Name | Description | Status |
|---|---|---|
| `test_customer_registration` | Validates registration, customer profile generation, and bcrypt hashing. | PASSED |
| `test_driver_registration` | Validates public driver registration. | PASSED |
| `test_reject_public_admin_registration` | Prevents unauthorized self-escalation to ADMIN (403 Forbidden). | PASSED |
| `test_duplicate_email_registration` | Prevents duplicate user accounts (400 Bad Request). | PASSED |
| `test_login_success` | Verifies password verification and signed JWT token issuance. | PASSED |
| `test_login_invalid_password` | Verifies rejection of wrong passwords (401 Unauthorized). | PASSED |
| `test_login_inactive_user` | Rejects deactivated accounts (403 Forbidden). | PASSED |
| `test_get_me_endpoint` | Verifies `/api/v1/auth/me` returns authenticated user profile. | PASSED |
| `test_rbac_admin_endpoint_protection` | **Critical RBAC:** Customers/Drivers receive 403 on `/api/v1/users`; Admin receives 200. | PASSED |
| `test_change_password` | Verifies password change workflow and login with updated credentials. | PASSED |

### System Health & Security Suite (`backend/tests/test_health.py`)
| Test Name | Description | Status |
|---|---|---|
| `test_root_endpoint` | Validates root status, version, and documentation links. | PASSED |
| `test_health_ping` | Validates lightweight `/ping` endpoint. | PASSED |
| `test_comprehensive_health` | Validates database connectivity, latency calculation, and process metrics. | PASSED |
| `test_password_hashing_and_verification` | Validates bcrypt salting, hashing, and matching. | PASSED |
| `test_jwt_token_lifecycle` | Validates token creation, claims encoding, and signature decoding. | PASSED |
| `test_jwt_token_invalid_signature` | Validates that tampered tokens trigger cryptographic rejection. | PASSED |

Total Executed: **16 Tests**, Passed: **16 (100%)**, Failed: **0**, Skipped: **0**.
