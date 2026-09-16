import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from .config import settings

def generate_uuid() -> str:
    return str(uuid.uuid4())

# Configure Engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True
)

SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
ScopedSession = scoped_session(SessionFactory)
Base = declarative_base()

def get_db():
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models to ensure they are registered with Base.metadata
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
