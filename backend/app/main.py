"""
FastAPI application entrypoint: wires up CORS, routers, startup DB init,
and global error handlers.

Run with:  uvicorn app.main:app --reload
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.connection import init_db
from app.api import auth, resumes, jobs, analysis, dashboard, generated_resumes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Multi-Agent AI Resume Screening and ATS Analysis System",
    description=(
        "A multi-agent AI system that analyzes a resume against a job description, "
        "producing an AI-estimated ATS compatibility score and job match score via a "
        "hybrid LLM + deterministic scoring architecture. Not a substitute for human "
        "hiring judgment."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        init_db()
        logger.info("Database tables verified/created.")
    except Exception as exc:  # noqa: BLE001
        logger.error("Database initialization failed: %s", exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})


app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(generated_resumes.router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Resume Screening API is running"}