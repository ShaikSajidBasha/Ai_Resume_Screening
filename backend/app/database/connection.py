"""
SQLAlchemy engine/session setup for MySQL, plus a FastAPI dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# pool_pre_ping avoids "MySQL server has gone away" on idle connections
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call once at startup (or use Alembic in production)."""
    from app.models import user, resume, job_description, analysis, agent_result, generated_resume  # noqa: F401
    Base.metadata.create_all(bind=engine)
