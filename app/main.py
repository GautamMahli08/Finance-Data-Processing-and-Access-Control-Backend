"""
Finance Dashboard Backend API
- FastAPI + MongoDB (Motor async)
- JWT Bearer Authentication
- Role Based Access Control (Viewer / Analyst / Admin)
- Rate Limiting via slowapi
- Soft Delete for records
- Audit Logging for all write actions
- Pagination + Search + Filters
- Change Password for own account
- Swagger docs at /docs | ReDoc at /redoc
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.database import connect_db, close_db, seed_db
from app.api import auth, users, records, dashboard, audit
import uuid, time

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await seed_db()
    yield
    await close_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description="""
## Finance Dashboard Backend API

Role-based access control backend for managing financial records.

---

### 👤 Roles & Permissions

| Role | View Records | Dashboard Summary | Dashboard Insights | Create/Update/Delete Records | Manage Users | Audit Logs |
|---|---|---|---|---|---|---|
| **Viewer** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Analyst** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ (own only) |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (all) |

---

### 🔐 Authentication
All endpoints (except `/auth/login`) require a Bearer token:
```
Authorization: Bearer <token>
```
Click the **Authorize** button above and paste your token.

---

### 🔍 Search & Filter Records
```
GET /api/v1/records?search=salary          # partial match in notes/category
GET /api/v1/records?type=expense
GET /api/v1/records?category=Rent
GET /api/v1/records?date_from=2025-01-01&date_to=2025-03-31
GET /api/v1/records?page=2&page_size=10
```

---

### ⚡ Rate Limits
| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 10 requests/minute per IP |
| All other endpoints | 200 requests/minute per IP |

---

### 📋 Audit Logs
Every create, update, delete action is logged with who did it and when.
`GET /api/v1/audit` — Admin sees all logs, Analyst sees own actions only.

---

### 🔑 Seeded Admin Credentials
| Email | Password |
|---|---|
| `admin@finance.dev` | `Admin@123` |
""",
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attaches a unique X-Request-ID to every response for tracing"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"]    = request_id
    response.headers["X-Process-Time"]  = f"{process_time}ms"
    return response

# ── Validation error handler ───────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "detail": "Validation failed",
        "errors": [
            {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
    })

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/v1")
app.include_router(users.router,     prefix="/api/v1")
app.include_router(records.router,   prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(audit.router,     prefix="/api/v1")

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app":    settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs":   "/docs",
        "redoc":  "/redoc",
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
