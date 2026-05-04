from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load environment variables from .env file before importing app modules
load_dotenv()

from app.config import settings
from app.routers import auth, jobs, users, companies, applications, saved_jobs, job_alerts, dashboard, skills

app = FastAPI(
    title="Foundit Clone API",
    description=(
        "Production-grade REST API for the Foundit.in job portal clone. "
        "Supports job seekers and employers with full job search, applications, "
        "company profiles, alerts, and dashboard analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
allowed_origins = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(users.router)
app.include_router(companies.router)
app.include_router(applications.router)
app.include_router(saved_jobs.router)
app.include_router(job_alerts.router)
app.include_router(dashboard.router)
app.include_router(skills.router)

# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint — returns API status and version."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "version": "1.0.0",
            "service": "Foundit Clone API",
        },
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — redirects to API docs."""
    return JSONResponse(
        content={
            "message": "Welcome to Foundit Clone API",
            "docs": "/docs",
            "health": "/health",
        }
    )


# ---------------------------------------------------------------------------
# Global exception handler for unhandled errors
# ---------------------------------------------------------------------------
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        messages.append(f"{loc}: {msg}" if loc else msg)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "data": {"errors": messages},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "data": None,
        },
    )
