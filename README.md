# Finance Dashboard Backend API

A production-ready role-based access control backend for financial records management, built with **FastAPI** and **MongoDB**.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Database | MongoDB + Motor (async) |
| Auth | JWT Bearer Token (python-jose) |
| Password | bcrypt (passlib) |
| Validation | Pydantic v2 |
| Rate Limiting | slowapi |
| Testing | pytest + httpx |
| Version used |Python 3.10.0 |

---

## Project Structure

```
finance-backend/
├── app/
│   ├── main.py                     # App entry, middleware, lifespan
│   ├── api/
│   │   ├── auth.py                 # POST /auth/login (rate limited)
│   │   ├── users.py                # User CRUD + change-password
│   │   ├── records.py              # Records CRUD + filter + search + pagination
│   │   ├── dashboard.py            # Summary + Insights
│   │   └── audit.py                # Audit log viewer
│   ├── core/
│   │   ├── config.py               # Settings from env vars (pydantic-settings)
│   │   ├── database.py             # Motor client, indexes, admin seed
│   │   ├── deps.py                 # Dependency injection (JWT + RBAC)
│   │   └── security.py             # JWT encode/decode, bcrypt hash/verify
│   ├── models/
│   │   └── enums.py                # Role, RecordType enums
│   ├── schemas/
│   │   ├── user.py                 # UserCreate, UserOut, TokenResponse, ChangePasswordRequest
│   │   └── record.py               # RecordCreate, RecordUpdate, RecordOut, RecordFilter
│   └── services/
│       ├── auth_service.py         # Login, token verification, login audit log
│       ├── user_service.py         # User CRUD + audit logging
│       ├── record_service.py       # Record CRUD + aggregations + audit logging
│       └── audit_service.py        # Append-only audit log writer + reader
├── tests/
│   ├── test_auth.py                # Login, wrong password, missing fields, token checks
│   ├── test_users.py               # Create, duplicate, weak password, RBAC
│   └── test_records.py             # CRUD, filters, search, soft delete, RBAC, dashboard
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Setup & Run


### 1. Install dependencies
```bash
python -m venv venv
venv\Scripts\activate
py -3.11 pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set ADMIN_EMAIL, ADMIN_PASSWORD, SECRET_KEY
```

### 3. Run server
```bash
uvicorn app.main:app --reload
```

| URL | Description |
|---|---|
| http://localhost:8000 | Root health check |
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc documentation |

---

## Seeded Credentials

On first startup with an empty MongoDB, one admin user is created from `.env` values:

| Email | Password |
|---|---|
| `admin@finance.dev` | `Admin@123` |

All other users must be created manually via `POST /api/v1/users` by the admin.

---

## Role Permission Matrix

| Action | Viewer | Analyst | Admin |
|---|---|---|---|
| Login | ✅ | ✅ | ✅ |
| View own profile (`GET /users/me`) | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |
| View records | ✅ | ✅ | ✅ |
| Dashboard summary | ✅ | ✅ | ✅ |
| Dashboard insights | ❌ | ✅ | ✅ |
| View own audit logs | ❌ | ✅ | ✅ |
| Create / Update / Delete records | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |
| View all audit logs | ❌ | ❌ | ✅ |

---

## API Endpoints

All routes are prefixed with `/api/v1`

### Auth
| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| POST | `/auth/login` | Get JWT token | 10/min |

### Users
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/users/me` | Get own profile | All |
| POST | `/users/me/change-password` | Change own password | All |
| GET | `/users` | List all users | Admin |
| POST | `/users` | Create user | Admin |
| GET | `/users/{id}` | Get user by ID | Admin |
| PATCH | `/users/{id}` | Update name/role/status | Admin |
| DELETE | `/users/{id}` | Deactivate user (soft) | Admin |

### Records
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/records` | List with filter/search/pagination | All |
| POST | `/records` | Create record | Admin |
| GET | `/records/{id}` | Get single record | All |
| PATCH | `/records/{id}` | Update record | Admin |
| DELETE | `/records/{id}` | Soft delete record | Admin |

**Query params for `GET /records`:**
```
?type=income|expense
?category=Rent
?date_from=2025-01-01&date_to=2025-03-31
?search=salary          ← partial match in category + notes
?page=1&page_size=20
```

### Dashboard
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/dashboard/summary` | Total income, expenses, net balance, trends | All |
| GET | `/dashboard/insights` | Month-over-month changes, top expense category | Analyst + Admin |

### Audit Logs
| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/audit` | View audit logs | Analyst (own), Admin (all) |

---

## System Design

### Architecture: Layered
```
API Layer      → routes, HTTP status codes, request/response
Service Layer  → business logic, validation, audit logging
Data Layer     → MongoDB queries via Motor async driver
```

### Patterns Used
| Pattern | Where |
|---|---|
| Layered Architecture | API → Service → DB |
| Dependency Injection | FastAPI Depends() for auth + RBAC |
| Soft Delete | records.is_deleted flag |
| Audit Log (append-only) | audit_logs collection |
| DTO / Schema Separation | UserCreate / UserOut (password never leaked) |
| Middleware Chain | Rate limit → CORS → Request ID → Auth → Route |
| 12-Factor Config | All secrets from .env / environment variables |

---

## Password Requirements

All passwords must have:
- Minimum 8 characters
- At least one uppercase letter
- At least one digit (0–9)
- At least one special character (`@$!%*#?&`)

---

## Response Headers (every request)

```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000   ← for tracing
X-Process-Time: 12.5ms                                ← for performance monitoring
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Generate a Strong SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Assumptions Made

1. `date` field in records is stored as `YYYY-MM-DD` string (simple, sortable, no timezone issues)
2. Soft-deleted records are invisible to all users but remain in DB for audit trail
3. Admin cannot deactivate their own account (safety guard)
4. Analyst sees only their own audit logs; Admin sees all
5. Rate limiting is in-memory (resets on server restart) — for production use Redis backend
6. MongoDB is used as document store; no joins needed given the simple data model

---

## Tradeoffs

| Decision | Tradeoff |
|---|---|
| In-memory rate limiting | Simple setup; not distributed — use Redis in production |
| UUID as `id` field | Portable across DBs; slightly larger than ObjectId |
| String date (`YYYY-MM-DD`) | Easy to filter/sort; no timezone complexity for finance use case |
| Motor async driver | Full async; requires async context (no sync usage) |
